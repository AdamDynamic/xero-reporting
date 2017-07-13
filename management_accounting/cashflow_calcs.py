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
import references as r
import utils.data_integrity
from utils.db_connect import db_sessionmaker
import utils.misc_functions


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

def get_all_bs_nodes_unmapped_for_cashflow():
    ''' Checks that the L2 nodes in the Balance Sheet are all captured by one of the three categories of nodes
        (operating, investment, financing) used to calculate the cash flows of the business

    :return:
    '''

    session = db_sessionmaker()
    qry = session.query(TableFinancialStatements,
                                TableChartOfAccounts,
                                TableNodeHierarchy)\
        .filter(TableFinancialStatements.AccountCode==TableChartOfAccounts.ClearmaticsCode)\
        .filter(TableChartOfAccounts.L3Code==TableNodeHierarchy.L3Code)\
        .all()

    session.close()

    b2_L2_nodes = list(set([node.L2Code for fs, coa, node in qry if node.L0Name==r.CM_DATA_BALANCESHEET]))
    unmapped_nodes = []
    for node in b2_L2_nodes:
        if node not in r.CM_BS_L2_OPERATING:
            if node not in r.CM_BS_L2_INVESTMENT:
                if node not in r.CM_BS_L2_FINANCING:
                    if node not in r.CM_BS_L2_EXCLUDED:
                        unmapped_nodes.append(node)

    return unmapped_nodes

def calculate_cashflow_from_operations(year, month, data_rows):
    ''' Uses the indirect method to calculate the indirect cash flow for a period

    :param data_rows: A list of TableConsolidatedFinStatements row objects
    :return: Float value of cash flow from operations for period given
    '''

    current_period = datetime.datetime(year=year, month=month, day=1)
    rows_to_upload = []
    list_of_companies = list(set([row.CompanyCode for row in data_rows]))   # Create for list of companies to future-proof
    for company in list_of_companies:

        operating_cash_flow = 0

        net_income = sum([row.Value for row in data_rows if row.FinancialStatement==r.CM_DATA_INCOMESTATEMENT
                          and row.CompanyCode==company and row.Period==current_period])  # ToDo: Magic numbers
        operating_cash_flow += net_income
        print net_income

        # Add back depreciation (IS)
        depreciation = sum([row.Value for row in data_rows if row.L2Code==r.CM_IS_L2_DEPRECIATION
                            and row.Period==current_period and row.CompanyCode==company])
        operating_cash_flow -= depreciation
        print depreciation

        # Add back deferred taxes (IS)
        deferred_tax = sum([row.Value for row in data_rows if row.L2Code == r.CM_IS_L2_DEFTAXES
                            and row.Period == current_period and row.CompanyCode==company])
        operating_cash_flow -= deferred_tax
        print deferred_tax

        # For every L2 node in the Balance Sheet identified as being part of operating cash flow, calculate the
        # difference in the balance between two periods and use to adjust operating cash flow
        for cost_node in r.CM_BS_L2_OPERATING:
            change_in_balance = calculate_change_in_balancesheet_value(year=year,
                                                                       month=month,
                                                                       company=company,
                                                                       bs_L2_node=cost_node,
                                                                       data_rows=data_rows)
            operating_cash_flow -= change_in_balance
            print change_in_balance

        # For each company, create a row for upload to the Financial Statements table
        new_row = TableFinancialStatements(
            TimeStamp=None,
            CompanyCode=company,
            CostCentreCode=None,
            Period=current_period,
            AccountCode=r.CM_CF_GL_OPERATING, # ToDo: Magic Number
            Value=operating_cash_flow
        )
        rows_to_upload.append(new_row)

        print "Operating: ", operating_cash_flow

    return rows_to_upload

def calculate_cashflow_from_investment(year, month, data_rows):
    ''' Uses the indirect method to calculate the indirect cash flow for a period

    :param data_rows: A list of TableConsolidatedFinStatements row objects
    :return: Float value of cash flow from investments for period given
    '''

    current_period = datetime.datetime(year=year, month=month, day=1)
    list_of_companies = list(set([row.CompanyCode for row in data_rows]))   # Create for list of companies to future-proof
    investment_cash_flow = 0
    rows_to_upload = []

    for company in list_of_companies:

        # Add back depreciation (IS)
        depreciation = sum([row.Value for row in data_rows if row.L2Code == r.CM_IS_L2_DEPRECIATION
                            and row.Period == current_period and row.CompanyCode==company])
        investment_cash_flow -= depreciation

        for cost_node in r.CM_BS_L2_INVESTMENT:
            change_in_balance = calculate_change_in_balancesheet_value(year=year,
                                                                       month=month,
                                                                       company=company,
                                                                       bs_L2_node=cost_node,
                                                                       data_rows=data_rows)
            investment_cash_flow -= change_in_balance
            print change_in_balance

        # For each company, create a row for upload to the Financial Statements table
        new_row = TableFinancialStatements(
            TimeStamp=None,
            CompanyCode=company,
            CostCentreCode=None,
            Period=current_period,
            AccountCode=r.CM_CF_GL_INVESTMENT, # ToDo: Magic Number
            Value=investment_cash_flow
        )
        rows_to_upload.append(new_row)

        print "Investment: ", investment_cash_flow
    return rows_to_upload

def calculate_cashflow_from_financing(year, month, data_rows):
    ''' Uses the indirect method to calculate the indirect cash flow for a period

    :param data_rows: A list of TableConsolidatedFinStatements row objects
    :return: Float value of cash flow from financing for period given
    '''

    list_of_companies = list(set([row.CompanyCode for row in data_rows]))   # Create for list of companies to future-proof
    financing_cash_flow = 0
    rows_to_upload = []

    for company in list_of_companies:
        for cost_node in r.CM_BS_L2_FINANCING:
            change_in_balance = calculate_change_in_balancesheet_value(year=year,
                                                                       month=month,
                                                                       company=company,
                                                                       bs_L2_node=cost_node,
                                                                       data_rows=data_rows)
            financing_cash_flow -= change_in_balance
            print change_in_balance

        # For each company, create a row for upload to the Financial Statements table
        new_row = TableFinancialStatements(
            TimeStamp=None,
            CompanyCode=company,
            CostCentreCode=None,
            Period=datetime.datetime(year=year, month=month, day=1),
            AccountCode=r.CM_CF_GL_FINANCING, # ToDo: Magic Number
            Value=financing_cash_flow
        )
        rows_to_upload.append(new_row)

        print "Financing: ", financing_cash_flow
    return rows_to_upload

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

    # Get Income Statement and Balance Sheet split by L0 and L1 node
    session = db_sessionmaker()

    data = session.query(TableFinancialStatements, TableChartOfAccounts, TableNodeHierarchy)\
        .filter(TableFinancialStatements.AccountCode==TableChartOfAccounts.ClearmaticsCode)\
        .filter(TableChartOfAccounts.L3Code==TableNodeHierarchy.L3Code)\
        .filter(TableFinancialStatements.Period<=current_period)\
        .filter(TableFinancialStatements.Period>=prior_period)\
        .all()

    session.close()

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
                                                GLAccountCode = coa.ClearmaticsCode,
                                                GLAccountName = coa.ClearmaticsName,
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

    # Calculate the periodic movements of each cash flow statement category and create database row objects
    unmapped_nodes = get_all_bs_nodes_unmapped_for_cashflow()
    if unmapped_nodes != []:
        raise error_objects.MasterDataIncompleteError("Balance sheet nodes not found in master lists:\n{}"
                                                      .format(unmapped_nodes))

    cash_flow_rows = []
    cash_flow_rows += calculate_cashflow_from_operations(year=year, month=month, data_rows=calc_rows)
    cash_flow_rows += calculate_cashflow_from_investment(year=year, month=month, data_rows=calc_rows)
    cash_flow_rows += calculate_cashflow_from_financing(year=year, month=month, data_rows=calc_rows)
    print "Total Calc: ", sum([row.Value for row in cash_flow_rows])
    # Temp check:
    total_cash = calculate_change_in_balancesheet_value(year=year, month=month, company=1000, bs_L2_node='L2A-CASH', data_rows=calc_rows)
    print "BS Cash Difference: ", total_cash

    # ToDo: Need to check whether previous period Balance Sheet is available

    # ToDo: Perform check that calculated cash flow equals change in cash balances

    return cash_flow_rows



#create_internal_cashflow_statement(year=2017, month=4)