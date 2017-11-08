#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains functions designed to check the integrity of the data
'''

import datetime
import os

import sqlalchemy

from customobjects import error_objects
from customobjects.database_objects import \
    TableChartOfAccounts, \
    TableAllocationAccounts, \
    TableCostCentres, \
    TableCompanies, \
    TableNodeHierarchy, \
    TablePeriods, \
    TableFinancialStatements, \
    TableXeroExtract, \
    TableFinModelExtract
from utils.db_connect import db_sessionmaker
import references as r
import references_private as rp

def check_unassigned_costcentres_is_nil(year, month):
    ''' Checks that any L1 nodes that must reallocate its costs has no costs that have no cost centre allocated

    :param year: Year of the period to check
    :param month: Month of the period to check
    :return:
    '''

    session = db_sessionmaker()
    date_to_check = datetime.datetime(year=year, month=month, day=1)

    total_unassigned = session.query(TableXeroExtract, TableChartOfAccounts, TableNodeHierarchy, TableAllocationAccounts)\
        .filter(TableXeroExtract.AccountCode==TableChartOfAccounts.XeroCode)\
        .filter(TableChartOfAccounts.L3Code==TableNodeHierarchy.L3Code)\
        .filter(TableNodeHierarchy.L2Code == TableAllocationAccounts.L2Hierarchy)\
        .filter(TableXeroExtract.CostCentreName == rp.XERO_UNASSIGNED_CC) \
        .filter(TableXeroExtract.Period==date_to_check)\
        .all()
    session.close()

    L1_nodes = list(set([node.L1Code for xero, coa, node, alloc_ac in total_unassigned]))

    is_error = False
    consolidated_error_message = ""
    # Each L1 node should net to zero so that no unassigned costs are allocated to receiver cost centres
    for L1_node in L1_nodes:
        total_unallocated = sum([xero.Value for xero, coa, node, alloc_ac in total_unassigned if node.L1Code==L1_node])
        if abs(total_unallocated) > r.DEFAULT_MAX_CALC_ERROR:
            is_error = True
            consolidated_error_message += "Costs in cost centre '{}' for L1 node {} are not net flat for period {}.{} (total = {})\n"\
                .format(rp.XERO_UNASSIGNED_CC, L1_node, year, month, total_unallocated)

    if is_error:
        raise error_objects.UnallocatedCostsNotNilError("The Xero data contains the following unassigned balances:\n{}"
                                                        .format(consolidated_error_message))

def confirm_table_column_is_unique(table_object, column_name):
    ''' Confirms whether all the entries in a table column are unique (relevant for master data mappings)

    :param table_object: The sqlalchemy ORM object of the table
    :param column_name: Text description of the column name
    :return: True if all entries in the column name are unique
    '''

    session = db_sessionmaker()
    qry = session.query(table_object).all()
    session.close()

    table_keys = table_object.__table__.columns.keys()
    test_field = []
    for row in qry:
        a = {name: getattr(row, name) for name in table_keys}
        test_field.append(a[column_name])

    return len(test_field) == len(list(set(test_field)))

def check_budget_accounts_in_coa():
    ''' Checks that the GL accounts used in the Budget data are found in the main chart of accounts

    :return:
    '''

    # Get all GLs used in the Budget and in the Chart of Accounts
    session = db_sessionmaker()
    budget_accounts = session.query(TableFinModelExtract.GLCode).all()
    coa_accounts = session.query(TableChartOfAccounts.GLCode).all()
    session.close()

    # Unique values only
    budget_accounts = list(set(budget_accounts))

    missing_accounts = []
    for budget_account in budget_accounts:
        if budget_account not in coa_accounts:
            missing_accounts.append(budget_account)
    if missing_accounts:
        account_error_message = ""
        for missing_account in missing_accounts:
            account_error_message += str(missing_account) + "\n"
            raise error_objects.MasterDataIncompleteError("GL Accounts included in {} are missing from the Chart of Account in {}:\n{}"
                                                          .format(r.TBL_DATA_EXTRACT_FINMODEL, r.TBL_MASTER_CHARTOFACCOUNTS,
                                                                  account_error_message))

def check_table_has_records_for_period(year, month, table):
    ''' Checks whether a table contains a non-zero number of records for a given period

    :param year:
    :param month:
    :param table:
    :return:
    '''

    check_period_exists(year=year, month=month)
    period_to_check = datetime.datetime(year=year, month=month, day=1)
    session = db_sessionmaker()
    result = session.query(table).filter(table.Period == period_to_check).all()
    session.close()
    if result == []:
        raise error_objects.TableEmptyForPeriodError(
            "Table {} contains no records for period {}.{}".format(table.__tablename__, year, month))

def master_data_uniquesness_check():
    ''' Performs integrity checks on the master data in the table and raises an MasterDataIncompleteError if any
        duplicate values are detected in fields where each record should be unique.

    :return:
    '''

    consolidated_error_message = ""
    is_error = False

    if not confirm_table_column_is_unique(TableChartOfAccounts, r.COL_CHARTACC_GLCODE):
        is_error = True
        consolidated_error_message += "\n    Table {} has duplicate values in column {}"\
            .format(TableChartOfAccounts.__tablename__, r.COL_CHARTACC_GLCODE)

    if not confirm_table_column_is_unique(TableAllocationAccounts, r.COL_ALLOCACC_CODE):
        is_error = True
        consolidated_error_message += "\n    Table {} has duplicate values in column {}"\
                                                      .format(TableAllocationAccounts.__tablename__, r.COL_ALLOCACC_CODE)

    if not confirm_table_column_is_unique(TableCostCentres, r.COL_CC_CODE):
        is_error = True
        consolidated_error_message += "\n    Table {} has duplicate values in column {}"\
                                                      .format(TableCostCentres.__tablename__, r.COL_CC_CODE)

    if not confirm_table_column_is_unique(TableCompanies, r.COL_COMPANIES_COMPCODE):
        is_error = True
        consolidated_error_message += "\n    Table {} has duplicate values in column {}"\
                                                      .format(TableCompanies.__tablename__, r.COL_COMPANIES_COMPCODE)

    if not confirm_table_column_is_unique(TableNodeHierarchy, r.COL_NODE_L3CODE):
        is_error = True
        consolidated_error_message += "\n    Table {} has duplicate values in column {}"\
                                                      .format(TableNodeHierarchy.__tablename__, r.COL_NODE_L3CODE)

    if not confirm_table_column_is_unique(TablePeriods, r.COL_PERIOD_PERIOD):
        is_error = True
        consolidated_error_message += "\n    Table {} has duplicate values in column {}"\
                                                      .format(TablePeriods.__tablename__, r.COL_PERIOD_PERIOD)
    if is_error:
        raise error_objects.MasterDataIncompleteError("The Master Data contains the following errors:\n{}"
                                                      .format(consolidated_error_message))

def coa_L3_nodes_in_hierarchy():
    ''' Checks that all L3 nodes used in the CoA are found in the node hierarchy table

    :return:
    '''

    # Get all L3 nodes used in the CoA and in the hierarchy mapping table
    session = db_sessionmaker()
    L3_nodes = session.query(TableChartOfAccounts.L3Code).all()
    hierarchy_nodes = session.query(TableNodeHierarchy.L3Code).all()
    session.close()

    # Check that each L3 node used in the CoA is also included in the hierarchy
    L3_nodes = list(set(L3_nodes))
    missing_nodes = []
    for node in L3_nodes:
        if node not in hierarchy_nodes:
            missing_nodes.append(node)
    if missing_nodes:
        node_error_message = ""
        for node in missing_nodes:
            node_error_message += str(node) + "\n"
        raise error_objects.MasterDataIncompleteError("L3 hierarchy nodes included in {} are missing from the mapping in {}:\n{}"
                                                      .format(r.TBL_MASTER_CHARTOFACCOUNTS, r.TBL_MASTER_NODEHIERARCHY, node_error_message))

def get_all_bs_nodes_unmapped_for_cashflow():
    ''' Checks that the L2 nodes in the Balance Sheet are all captured by one of the three categories of nodes
        (operating, investment, financing) used to calculate the cash flows of the business

    :return:
    '''

    session = db_sessionmaker()
    qry = session.query(TableFinancialStatements,
                                TableChartOfAccounts,
                                TableNodeHierarchy)\
        .filter(TableFinancialStatements.AccountCode == TableChartOfAccounts.GLCode)\
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

def get_unmapped_xero_account_codes():
    ''' Returns a summary of all Xero account codes not mapped to an internal, master Chart of Accounts code

    :return:
    '''

    session = db_sessionmaker()
    xero_data = session.query(TableXeroExtract).all()
    coa_data = session.query(TableChartOfAccounts).all()
    mapped_xero_codes = list(set([row.XeroCode for row in coa_data]))
    unmapped_rows = [(row.AccountName, row.AccountCode) for row in xero_data if row.AccountCode not in mapped_xero_codes]
    session.close()
    return unmapped_rows

def check_period_is_locked(year, month):
    ''' Checks whether a period in the reporting database is locked for changes

    :param year:
    :param month:
    :return: True/False depending on whether the period is locked or not
    '''

    check_period_exists(year=year, month=month)
    session = db_sessionmaker()
    date_to_check = datetime.datetime(year=year, month=month, day=1)
    lock_check = session.query(TablePeriods).filter(TablePeriods.Period==date_to_check).one()
    session.close()
    if lock_check.IsLocked:
        raise error_objects.PeriodIsLockedError("Period {}.{} is LOCKED in table {}".format(year, month, TablePeriods.__tablename__))
    else:
        return True

def check_period_exists(year, month):
    ''' Checks that the period is included in the database

    :param year:
    :param month:
    :return:
    '''

    # Check that the inputs are basically correct (i.e. year in sensible range, month between 1 and 12)
    if (year in r.AVAILABLE_PERIODS_YEARS):
        if (month in r.AVAILABLE_PERIODS_MONTHS):
            pass
        else:
            raise  error_objects.PeriodNotFoundError("Month {} is not included in range of valid inputs: {}".format(month, r.AVAILABLE_PERIODS_MONTHS))
    else:
        raise error_objects.PeriodNotFoundError("Year {} is not included in range of valid inputs: {}".format(year, r.AVAILABLE_PERIODS_YEARS))

    # Check that the period exists in the database Periods table
    try:
        session = db_sessionmaker()
        period_to_update = datetime.datetime(year=year, month=month, day=1)
        period_check = session.query(TablePeriods) \
            .filter(TablePeriods.Period == period_to_update) \
            .one()
    except sqlalchemy.orm.exc.NoResultFound:
        raise error_objects.PeriodNotFoundError("Period {}.{} does not exist in table {}"
                                                .format(year, month, TablePeriods.__tablename__))
    else:
        return True
    finally:
        session.close()

def check_directory_exists(dir_path):
    ''' Returns True/False on whether a given directory path exists

    :param dir_path:
    :return:
    '''

    return os.path.isdir(dir_path)

def balance_sheet_balances_check():
    ''' Checks whether the Balance Sheet nets to zero in the re-mapped financial data

    :return:
    '''

    session = db_sessionmaker()
    qry = session.query(TableFinancialStatements, TableChartOfAccounts, TableNodeHierarchy)\
        .filter(TableFinancialStatements.AccountCode == TableChartOfAccounts.GLCode)\
        .filter(TableChartOfAccounts.L3Code==TableNodeHierarchy.L3Code)\
        .filter(TableNodeHierarchy.L0Name==r.CM_DATA_BALANCESHEET).all()
    session.close()

    consolidated_error_message = ""
    is_error = False

    time_periods = list(set([fs.Period for fs, coa, node in qry]))

    for time_period in time_periods:
        imbalance_check = sum([fs.Value for fs, coa, node in qry if fs.Period==time_period])
        if imbalance_check != 0:
            is_error = True
            consolidated_error_message += "    Balance Sheet has imbalance of {} for period {}."\
                                                           .format(imbalance_check, time_period.date())

    if is_error:
        raise error_objects.BalanceSheetImbalanceError("The Balance Sheet contains the following errors:\n{}"
                                                       .format(consolidated_error_message))

def master_data_integrity_check_actuals(year, month, check_balance_sheet=True, check_unassigned_balances=True):
    ''' Performs a series of tests on the data to determine whether processes that depend on data integrity will work correctly

    :param year:
    :param month:
    :return:
    '''

    check_period_exists(year=year, month=month)
    check_period_is_locked(year=year, month=month)

    master_data_uniquesness_check()
    coa_L3_nodes_in_hierarchy()

    # Not necessary to check if pulling data from Xero
    if check_unassigned_balances:
        check_unassigned_costcentres_is_nil(year=year, month=month)

    # Where old data is overwritten, a balance sheet imbalance may be the error being corrected
    if check_balance_sheet:
        balance_sheet_balances_check()

def master_data_integrity_check_budget():
    ''' Performs tests on the data integrity of the Budget data

    :return:
    '''

    master_data_uniquesness_check()
    coa_L3_nodes_in_hierarchy()
    check_budget_accounts_in_coa()