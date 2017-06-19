#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains functions used to process external (i.e. Xero) data into standardised internal formats
'''

import datetime

from sqlalchemy.orm import aliased

from customobjects import error_objects
from customobjects.database_objects import \
    TableXeroExtract, \
    TableCompanies, \
    TableCostCentres, \
    TableChartOfAccounts, \
    TableProfitAndLoss, \
    TableConsolidatedIncomeStatement, \
    TableAllocationsData, TableAllocationAccounts
import references as r
from utils.db_connect import db_sessionmaker
import utils.misc_functions
import utils.xero_connect


def create_internal_profit_and_loss(year=None, month=None):
    ''' Creates the master-data version of the profit and loss from the imported xero data

    :param year:
    :param month:
    :return:
    '''

    # Perform validations on the data before proceeding
    utils.misc_functions.check_period_exists(year=year, month=month)
    utils.misc_functions.check_period_is_locked(year=year, month=month)
    utils.misc_functions.check_table_has_records_for_period(year=year, month=month, table=TableXeroExtract)

    # Check whether the cost centre field has been populated for all line items in the xero data
    cost_centres_populated = utils.xero_connect.check_unassigned_costcentres_is_nil(year=year, month=month)

    if cost_centres_populated:

        # Clear out previously-imported data from the table
        utils.misc_functions.delete_table_data_for_period(table=TableProfitAndLoss,year=year, month=month)

        timestamp = datetime.datetime.now()

        session = db_sessionmaker()
        period_to_extract = datetime.datetime(year=year, month=month, day=1)

        query = session.query(TableXeroExtract,  TableCompanies, TableCostCentres, TableChartOfAccounts)\
            .filter(TableXeroExtract.CompanyName==TableCompanies.XeroName)\
            .filter(TableXeroExtract.CostCentreName==TableCostCentres.XeroName)\
            .filter(TableXeroExtract.AccountCode==TableChartOfAccounts.XeroCode)\
            .filter(TableXeroExtract.Period==period_to_extract)\
            .all()
        if len(query)!=0:

            for xero_data, company, costcentre, account in query:
                if xero_data.Value != 0:
                    new_row = TableProfitAndLoss(
                                                TimeStamp = timestamp,
                                                CompanyCode = company.ClearmaticsCode,
                                                CostCentreCode = costcentre.ClearmaticsCode,
                                                Period = period_to_extract,
                                                AccountCode = account.ClearmaticsCode,
                                                Value = (xero_data.Value * account.XeroMultiplier)  # Xero outputs all balances as positive
                                                )
                    session.add(new_row)

            session.commit()
            session.close()

        else:
            raise error_objects.TableEmptyForPeriodError("No data returned from table {} for period {}.{}".format(r.TBL_DATA_XEROEXTRACT, year, month))
    else:
        raise ValueError("'Unassigned' cost centre in table {} does not sum to zero".format(r.TBL_DATA_XEROEXTRACT))

def create_consolidated_income_statement(year, month):
    ''' Creates the consolidated income statement that includes the allocated costs and readable cost centre, company mappings

    :param year:
    :param month:
    :return:
    '''

    # Perform validation checks before proceeding
    utils.misc_functions.check_period_exists(year=year, month=month)
    utils.misc_functions.check_period_is_locked(year=year, month=month)
    utils.misc_functions.check_table_has_records_for_period(year=year, month=month, table=TableProfitAndLoss)
    utils.misc_functions.check_table_has_records_for_period(year=year, month=month, table=TableAllocationsData)

    time_stamp = datetime.datetime.now()
    period_to_create = datetime.datetime(year=year, month=month,day=1)

    # Delete periodic data from the table
    utils.misc_functions.delete_table_data_for_period(table=TableConsolidatedIncomeStatement, year=year, month=month)

    session = db_sessionmaker()
    # Extract the data from the Xero Income Statement
    consol_qry = session.query(TableProfitAndLoss, TableCompanies, TableCostCentres, TableChartOfAccounts)\
        .filter(TableProfitAndLoss.Period==period_to_create)\
        .filter(TableProfitAndLoss.CompanyCode==TableCompanies.ClearmaticsCode)\
        .filter(TableProfitAndLoss.CostCentreCode==TableCostCentres.ClearmaticsCode)\
        .filter(TableProfitAndLoss.AccountCode==TableChartOfAccounts.ClearmaticsCode)\
        .all()

    assert consol_qry != [], "Query of Income Statement data produced no results"

    for pnl, comp, cc, coa in consol_qry:
        consol_row = TableConsolidatedIncomeStatement(
                                                    Period = period_to_create,
                                                    CompanyCode = comp.ClearmaticsCode,
                                                    CompanyName = comp.ClearmaticsName,
                                                    PartnerCompanyCode = None,
                                                    PartnerCompanyName = None,
                                                    CostCentreCode = cc.ClearmaticsCode,
                                                    CostCentreName = cc.ClearmaticsName,
                                                    PartnerCostCentreCode = None,
                                                    PartnerCostCentreName = None,
                                                    FinancialStatement = coa.L0Name,
                                                    GLAccountCode = coa.ClearmaticsCode,
                                                    GLAccountName = coa.ClearmaticsName,
                                                    L1HierarchyCode = coa.L1Code,
                                                    L1HierarchyName = coa.L1Name,
                                                    CostHierarchyNumber = cc.AllocationTier,
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
    alloc_qry = session.query(TableAllocationsData, comp_alias_sending, comp_alias_receiving, cc_alias_sending, cc_alias_receiving, TableAllocationAccounts)\
        .filter(TableAllocationsData.Period==period_to_create)\
        .filter(TableAllocationsData.SendingCompany==comp_alias_sending.ClearmaticsCode)\
        .filter(TableAllocationsData.ReceivingCompany==comp_alias_receiving.ClearmaticsCode)\
        .filter(TableAllocationsData.SendingCostCentre==cc_alias_sending.ClearmaticsCode)\
        .filter(TableAllocationsData.ReceivingCostCentre==cc_alias_receiving.ClearmaticsCode)\
        .filter(TableAllocationsData.GLAccount==TableAllocationAccounts.ClearmaticsCode)\
        .all()

    assert alloc_qry != [], "Allocation query produced no results"

    for data, comp_send, comp_rec, cc_send, cc_rec, alloc_accounts in alloc_qry:
        consol_row = TableConsolidatedIncomeStatement(
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
                                                    L1HierarchyCode = alloc_accounts.L1Code,
                                                    L1HierarchyName = alloc_accounts.L1Name,
                                                    CostHierarchyNumber = data.CostHierarchy,
                                                    Value = data.Value,
                                                    TimeStamp = time_stamp
                                                    )
        session.add(consol_row)

    session.commit()
    session.close()

#create_consolidated_income_statement(year=2017, month=5)