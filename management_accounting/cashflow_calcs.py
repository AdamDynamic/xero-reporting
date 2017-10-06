#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains functions used to calculate the cashflow statement of the company based on movements in the balance sheet
'''
import datetime

from dateutil.relativedelta import relativedelta

from customobjects import error_objects
from customobjects.database_objects import \
    TableFinancialStatements, \
    TableChartOfAccounts, \
    TableNodeHierarchy, \
    TableConsolidatedFinStatements
import utils.data_integrity
from utils.db_connect import db_sessionmaker
import utils.misc_functions
import references as r


def calculate_change_in_balancesheet_value(year, month, company, bs_L2_node, data_rows):
    ''' Calculates the change in a given node on the balance sheet between the given period and the period before.
        Function is used in the calculation of cash flows to back-calculate the cash movement for the period

    :param year:
    :param month:
    :param company:
    :param bs_L2_node:
    :param data_rows:
    :return:
    '''
    current_period = datetime.datetime(year=year, month=month, day=1)
    prior_period = current_period - relativedelta(months=1)

    current_period_total = sum([row.Value for row in data_rows if row.L2Code == bs_L2_node
                                and row.CompanyCode == company and row.Period == current_period])

    prior_period_total = sum([row.Value for row in data_rows if row.L2Code == bs_L2_node
                                and row.CompanyCode == company and row.Period == prior_period])

    change_in_balance = current_period_total - prior_period_total
    return change_in_balance

def calculate_cashflow_from_investment(year, month, data_rows, company_code):
    ''' Uses the indirect method to calculate the indirect cash flow for a period

    :param data_rows: A list of TableConsolidatedFinStatements row objects
    :return: Float value of cash flow from investments for period given
    '''

    current_period = datetime.datetime(year=year, month=month, day=1)
    investment_cash_flow = 0

    # Add back depreciation (IS)
    depreciation = sum([row.Value for row in data_rows if row.L2Code == r.CM_IS_L2_DEPRECIATION
                        and row.Period == current_period and row.CompanyCode==company_code])
    investment_cash_flow += depreciation

    for cost_node in r.CM_BS_L2_INVESTMENT:
        change_in_balance = calculate_change_in_balancesheet_value(year=year,
                                                                   month=month,
                                                                   company=company_code,
                                                                   bs_L2_node=cost_node,
                                                                   data_rows=data_rows)
        investment_cash_flow -= change_in_balance

    # For each company, create a row for upload to the Financial Statements table
    new_row = TableFinancialStatements(
        TimeStamp=None,
        CompanyCode=company_code,
        CostCentreCode=None,
        Period=current_period,
        AccountCode=r.CM_CF_GL_INVESTMENT, # ToDo: Magic Number
        Value=investment_cash_flow
        )

    return new_row

def calculate_cashflow_from_financing(year, month, data_rows, company_code):
    ''' Uses the indirect method to calculate the indirect cash flow for a period

    :param data_rows: A list of TableConsolidatedFinStatements row objects
    :return: Float value of cash flow from financing for period given
    '''

    current_period = datetime.datetime(year=year, month=month, day=1)
    financing_cash_flow = 0

    # Add back amortised interest expense
    amortised_interest = sum([row.Value for row in data_rows if row.L3Code == r.CM_IS_L3_NONCASHFINCHARGE
                        and row.Period == current_period and row.CompanyCode==company_code])
    financing_cash_flow += amortised_interest

    # Add back FX gains/losses
    fx_gains_losses = sum([row.Value for row in data_rows if row.L3Code == r.CM_IS_L3_FX_DEBT
                        and row.Period == current_period and row.CompanyCode==company_code])
    financing_cash_flow += fx_gains_losses

    for cost_node in r.CM_BS_L2_FINANCING:
        change_in_balance = calculate_change_in_balancesheet_value(year=year,
                                                                   month=month,
                                                                   company=company_code,
                                                                   bs_L2_node=cost_node,
                                                                   data_rows=data_rows)

        financing_cash_flow -= change_in_balance

    # For each company, create a row for upload to the Financial Statements table
    new_row = TableFinancialStatements(
        TimeStamp=None,
        CompanyCode=company_code,
        CostCentreCode=None,
        Period=datetime.datetime(year=year, month=month, day=1),
        AccountCode=r.CM_CF_GL_FINANCING, # ToDo: Magic Number
        Value=financing_cash_flow
    )

    return new_row

def calculate_company_cashflow(year, month, data_rows, company_code):
    '''

    :param year:
    :param month:
    :param data_rows:
    :param company_code:
    :return:
    '''
    current_period = datetime.datetime(year=year, month=month, day=1)
    output_rows = []

    company_data_rows = [row for row in data_rows if row.CompanyCode == company_code]
    financing_row = calculate_cashflow_from_financing(year=year, month=month,
                                                      data_rows=company_data_rows, company_code=company_code)
    investment_row = calculate_cashflow_from_investment(year=year, month=month,
                                                        data_rows=company_data_rows, company_code=company_code)

    change_in_cash_balance = calculate_change_in_balancesheet_value(year=year, month=month, company=company_code,
                                                                    bs_L2_node=r.CM_BS_CASH,
                                                                    data_rows=company_data_rows)

    # ToDo: Amend to reflect cash to/from revenues, employees and other
    cash_flow_from_operations = change_in_cash_balance - financing_row.Value - investment_row.Value

    operations_row = TableFinancialStatements(
        TimeStamp=None,
        CompanyCode=company_code,
        CostCentreCode=None,
        Period=current_period,
        AccountCode=r.CM_CF_GL_OPERATING,  # ToDo: Magic Number
        Value=cash_flow_from_operations
    )

    output_rows.append(operations_row)
    output_rows.append(financing_row)
    output_rows.append(investment_row)

    return output_rows

def create_internal_cashflow_statement(year, month):
    ''' Populates TableFinancialStatements with cash flow statement lines calculated indirectly using the
        indirect method.

    :param year:
    :param month:
    :return:
    '''

    current_period = datetime.datetime(year=year, month=month, day=1)
    prior_period = current_period - relativedelta(months=1)

    # Calculating cash flows based on Balance Sheet movements requires both the current period and the prior period
    # to be populated in the database (throws error if the prior period doesn't exist)
    utils.data_integrity.check_period_exists(year=prior_period.year, month=prior_period.month)

    # Get all Income Statement and Balance Sheet rows split by L0 and L1 node
    session = db_sessionmaker()

    data = session.query(TableFinancialStatements, TableChartOfAccounts, TableNodeHierarchy)\
        .filter(TableFinancialStatements.AccountCode == TableChartOfAccounts.GLCode)\
        .filter(TableChartOfAccounts.L3Code==TableNodeHierarchy.L3Code)\
        .filter(TableFinancialStatements.Period<=current_period)\
        .filter(TableFinancialStatements.Period>=prior_period)\
        .all()

    session.close()

    # Populate the data into standardised Consol Fin Statement rows
    calc_rows = []
    for fs, coa, node in data:
        new_row = TableConsolidatedFinStatements(
                                                ID = None,
                                                Period = fs.Period,
                                                CompanyCode = fs.CompanyCode,
                                                CompanyName = None,
                                                PartnerCompanyCode = None,
                                                PartnerCompanyName = None,
                                                CostCentreCode = None,
                                                CostCentreName = None,
                                                PartnerCostCentreCode = None,
                                                PartnerCostCentreName = None,
                                                FinancialStatement = node.L0Name,
                                                GLAccountCode = coa.GLCode,
                                                GLAccountName = coa.GLName,
                                                L1Code = node.L1Code,
                                                L1Name = node.L1Name,
                                                L2Code = node.L2Code,
                                                L2Name = node.L2Name,
                                                L3Code = node.L3Code,
                                                L3Name = node.L3Name,
                                                CostHierarchyNumber = None,
                                                Value = fs.Value,
                                                TimeStamp = fs.TimeStamp
                                                )
        calc_rows.append(new_row)

    # Check that all nodes in the standardised data are captured in the static master data
    unmapped_nodes = utils.data_integrity.get_all_bs_nodes_unmapped_for_cashflow()
    if unmapped_nodes != []:
        raise error_objects.MasterDataIncompleteError("Balance sheet nodes not found in master lists, cannot calculate cashflow:\n{}"
                                                      .format(unmapped_nodes))

    # Calculate the periodic movements of each cash flow statement category and create database row objects
    list_of_companies = list(set([row.CompanyCode for row in calc_rows]))  # Create for list of companies to future-proof

    cash_flow_rows = []
    for company in list_of_companies:
        cash_flow_rows += calculate_company_cashflow(year=year, month=month,
                                                     data_rows=calc_rows, company_code=company)

    # Check that the change in cash between two periods is the same as the calculated cashflow
    for company in list_of_companies:
        periodic_cash_change = calculate_change_in_balancesheet_value(year=year, month=month, company=company,
                                                                      bs_L2_node=r.CM_BS_CASH, data_rows=calc_rows)
        calculated_cash_change = sum([row.Value for row in cash_flow_rows if row.CompanyCode==company])

        if abs(calculated_cash_change-periodic_cash_change)>r.DEFAULT_MAX_CALC_ERROR:
            raise error_objects.CashFlowCalculationError(
                "Calculated indirect cash flow of {} in company {} is different for period change"
                " in values {} for period {}.{} "
                    .format(calculated_cash_change, company, periodic_cash_change, year, month))

    return cash_flow_rows