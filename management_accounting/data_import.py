#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains functions used to process external (i.e. Xero) data into standardised internal formats
'''

import datetime

from sqlalchemy.orm import aliased

import references as r
import utils.data_integrity
import utils.misc_functions
import utils.xero_connect
from customobjects import error_objects
from customobjects.database_objects import \
    TableXeroExtract, \
    TableCompanies, \
    TableCostCentres, \
    TableChartOfAccounts, \
    TableFinancialStatements, \
    TableConsolidatedFinStatements, \
    TableAllocationsData,\
    TableAllocationAccounts,\
    TableNodeHierarchy
from management_accounting.cashflow_calcs import create_internal_cashflow_statement
from utils.db_connect import db_sessionmaker
import utils.data_integrity


def create_internal_profit_and_loss(year, month):
    ''' Creates the rows for the master-data version of the profit and loss from the imported xero data

    :param year:
    :param month:
    :return: A list of TableFinancialStatements table row objects
    '''

    # Check whether the cost centre field has been populated for all line items in the xero data
    utils.xero_connect.check_unassigned_costcentres_is_nil(year=year, month=month)

    rows_to_upload = []
    session = db_sessionmaker()
    period_to_extract = datetime.datetime(year=year, month=month, day=1)

    query = session.query(TableXeroExtract,  TableCompanies, TableCostCentres, TableChartOfAccounts)\
        .filter(TableXeroExtract.CompanyName==TableCompanies.XeroName)\
        .filter(TableXeroExtract.CostCentreName==TableCostCentres.XeroName)\
        .filter(TableXeroExtract.AccountCode==TableChartOfAccounts.XeroCode)\
        .filter(TableXeroExtract.Period==period_to_extract)\
        .all()
    session.close()

    if len(query)==0:
        raise error_objects.TableEmptyForPeriodError("No data returned from table {} for period {}.{}".format(r.TBL_DATA_XEROEXTRACT, year, month))
    else:

        for xero_data, company, costcentre, account in query:
            if xero_data.Value != 0:
                new_row = TableFinancialStatements(
                                            TimeStamp = None,
                                            CompanyCode = company.ClearmaticsCode,
                                            CostCentreCode = costcentre.ClearmaticsCode,
                                            Period = period_to_extract,
                                            AccountCode = account.ClearmaticsCode,
                                            Value = (xero_data.Value * account.XeroMultiplier)  # Xero outputs all balances as positive
                                            )
                rows_to_upload.append(new_row)

    return rows_to_upload

def create_internal_balance_sheet(year, month):
    ''' Creates the master-data version of the balance sheet from the imported xero data

    :param year:
    :param month:
    :return:
    '''

    rows_to_upload = []
    session = db_sessionmaker()
    period_to_extract = datetime.datetime(year=year, month=month, day=1)

    query = session.query(TableXeroExtract,  TableCompanies, TableChartOfAccounts)\
        .filter(TableXeroExtract.ReportName==r.XERO_DATA_BALANCESHEET)\
        .filter(TableXeroExtract.CompanyName==TableCompanies.XeroName)\
        .filter(TableXeroExtract.AccountCode==TableChartOfAccounts.XeroCode)\
        .filter(TableXeroExtract.Period==period_to_extract)\
        .all()
    session.close()

    if len(query)==0:
        raise error_objects.TableEmptyForPeriodError("No data returned from table {} for period {}.{}".format(r.TBL_DATA_XEROEXTRACT, year, month))
    else:

        for xero_data, company, account in query:
            if xero_data.Value != 0:
                new_row = TableFinancialStatements(
                                            TimeStamp = None,
                                            CompanyCode = company.ClearmaticsCode,
                                            CostCentreCode = None,
                                            Period = period_to_extract,
                                            AccountCode = account.ClearmaticsCode,
                                            Value = (xero_data.Value * account.XeroMultiplier)  # Xero outputs all balances as positive
                                            )
                rows_to_upload.append(new_row)

    return rows_to_upload

def create_internal_financial_statements(year, month):
    ''' Creates an Income Statement, Balance Sheet and Cash Flow Statement, mapped to the Clearmatics internal
        master data mapping.

    :param year:
    :param month:
    :return:
    '''

    # Perform validations on the data before proceeding
    utils.data_integrity.master_data_integrity_check(year=year, month=month)
    utils.misc_functions.check_table_has_records_for_period(year=year, month=month, table=TableXeroExtract)

    # Create the P&L
    pnl_rows = create_internal_profit_and_loss(year=year, month=month)

    # Create the Balance Sheet
    bs_rows = create_internal_balance_sheet(year=year, month=month)

    # Create the Cash Flow Statement
    cf_rows = create_internal_cashflow_statement(year=year, month=month)

    # Create the Cash Flow Statement using P&L and Balance Sheet
    rows_to_upload = pnl_rows + bs_rows + cf_rows

    utils.misc_functions.delete_table_data_for_period(table=TableFinancialStatements, year=year, month=month)
    try:
        session = db_sessionmaker()
        timestamp = datetime.datetime.now()
        for row in rows_to_upload:
            row.TimeStamp = timestamp
            session.add(row)
    except Exception, e:
        raise
    else:
        session.commit()
    finally:
        session.close()

def create_consolidated_financial_statements(year, month):
    ''' Creates the consolidated financial statements that includes the allocated costs
        and readable cost centre, company mappings

    :param year:
    :param month:
    :return:
    '''
    # ToDo: Function feels too long - needs refactoring
    # Perform validation checks before proceeding
    utils.data_integrity.master_data_integrity_check(year=year, month=month)
    utils.misc_functions.check_table_has_records_for_period(year=year, month=month, table=TableFinancialStatements)
    utils.misc_functions.check_table_has_records_for_period(year=year, month=month, table=TableAllocationsData)

    time_stamp = datetime.datetime.now()
    period_to_create = datetime.datetime(year=year, month=month,day=1)

    # Delete periodic data from the table
    utils.misc_functions.delete_table_data_for_period(table=TableConsolidatedFinStatements, year=year, month=month)

    session = db_sessionmaker()
    # Extract the data from the Xero Income Statement
    consol_qry_cc = session.query(TableFinancialStatements,
                               TableCompanies,
                               TableCostCentres,
                               TableChartOfAccounts,
                               TableNodeHierarchy)\
        .filter(TableFinancialStatements.Period == period_to_create)\
        .filter(TableFinancialStatements.CompanyCode == TableCompanies.ClearmaticsCode)\
        .filter(TableFinancialStatements.CostCentreCode == TableCostCentres.ClearmaticsCode)\
        .filter(TableFinancialStatements.AccountCode == TableChartOfAccounts.ClearmaticsCode)\
        .filter(TableChartOfAccounts.L3Code == TableNodeHierarchy.L3Code)\
        .all()

    assert consol_qry_cc != [], "Query of financial statement (with costcentres) data produced no results"

    for pnl, comp, cc, coa , node in consol_qry_cc:
        consol_row = TableConsolidatedFinStatements(
                                                    Period = period_to_create,
                                                    CompanyCode = comp.ClearmaticsCode,
                                                    CompanyName = comp.ClearmaticsName,
                                                    PartnerCompanyCode = None,
                                                    PartnerCompanyName = None,
                                                    CostCentreCode = cc.ClearmaticsCode,
                                                    CostCentreName = cc.ClearmaticsName,
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
                                                    CostHierarchyNumber = cc.AllocationTier,
                                                    Value = pnl.Value,
                                                    TimeStamp = time_stamp
                                                    )
        session.add(consol_row)

    # Extract the data from the Xero financial statements (no cost centres e.g. Revenue, Balance Sheet)
    consol_qry_nocc = session.query(TableFinancialStatements,
                               TableCompanies,
                               TableChartOfAccounts,
                               TableNodeHierarchy)\
        .filter(TableFinancialStatements.Period == period_to_create)\
        .filter(TableFinancialStatements.CompanyCode == TableCompanies.ClearmaticsCode)\
        .filter(TableFinancialStatements.CostCentreCode == None)\
        .filter(TableFinancialStatements.AccountCode == TableChartOfAccounts.ClearmaticsCode)\
        .filter(TableChartOfAccounts.L3Code == TableNodeHierarchy.L3Code)\
        .all()

    assert consol_qry_nocc != [], "Query of financial statement data (no cost centres) produced no results"

    for pnl, comp, coa , node in consol_qry_nocc:
        consol_row = TableConsolidatedFinStatements(
                                                    Period = period_to_create,
                                                    CompanyCode = comp.ClearmaticsCode,
                                                    CompanyName = comp.ClearmaticsName,
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
                                                    Value = pnl.Value,
                                                    TimeStamp = time_stamp
                                                    )
        session.add(consol_row)

    # To reference a table more than once (sender, receiver cost centres) we need to alias the table
    cc_alias_sending = aliased(TableCostCentres)
    cc_alias_receiving = aliased(TableCostCentres)
    comp_alias_sending = aliased(TableCompanies)
    comp_alias_receiving = aliased(TableCompanies)

    # Append the data from the cost allocations table
    alloc_qry = session.query(TableAllocationsData,
                              comp_alias_sending,
                              comp_alias_receiving,
                              cc_alias_sending,
                              cc_alias_receiving,
                              TableAllocationAccounts)\
        .filter(TableAllocationsData.Period==period_to_create)\
        .filter(TableAllocationsData.SendingCompany==comp_alias_sending.ClearmaticsCode)\
        .filter(TableAllocationsData.ReceivingCompany==comp_alias_receiving.ClearmaticsCode)\
        .filter(TableAllocationsData.SendingCostCentre==cc_alias_sending.ClearmaticsCode)\
        .filter(TableAllocationsData.ReceivingCostCentre==cc_alias_receiving.ClearmaticsCode)\
        .filter(TableAllocationsData.GLAccount==TableAllocationAccounts.ClearmaticsCode)\
        .all()

    assert alloc_qry != [], "Allocation query produced no results"

    for data, comp_send, comp_rec, cc_send, cc_rec, alloc_accounts in alloc_qry:
        consol_row = TableConsolidatedFinStatements(
                                                    Period = period_to_create,
                                                    CompanyCode = comp_rec.ClearmaticsCode,
                                                    CompanyName = comp_rec.ClearmaticsName,
                                                    PartnerCompanyCode = comp_send.ClearmaticsCode,
                                                    PartnerCompanyName = comp_send.ClearmaticsName,
                                                    CostCentreCode = cc_rec.ClearmaticsCode,
                                                    CostCentreName = cc_rec.ClearmaticsName,
                                                    PartnerCostCentreCode = cc_send.ClearmaticsCode,
                                                    PartnerCostCentreName = cc_send.ClearmaticsName,
                                                    FinancialStatement = alloc_accounts.L0Name,
                                                    GLAccountCode = alloc_accounts.ClearmaticsCode,
                                                    GLAccountName = alloc_accounts.ClearmaticsName,
                                                    L1Code = alloc_accounts.L1Code,
                                                    L1Name = alloc_accounts.L1Name,
                                                    L2Code = alloc_accounts.L2Code,
                                                    L2Name = alloc_accounts.L2Name,
                                                    L3Code = alloc_accounts.L3Code,
                                                    L3Name = alloc_accounts.L3Name,
                                                    CostHierarchyNumber = data.CostHierarchy,
                                                    Value = data.Value,
                                                    TimeStamp = time_stamp
                                                    )
        session.add(consol_row)

    session.commit()
    session.close()