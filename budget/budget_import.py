#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains the functions used to import budget and forecast data as produced by the offline Financial Model
'''
import datetime

from dateutil import parser
from sqlalchemy.orm import aliased

import utils.console_output
from customobjects import error_objects
from customobjects.database_objects import \
    TableFinModelExtract, \
    TableCompanies, \
    TableChartOfAccounts, \
    TableNodeHierarchy, \
    TableCostCentres, \
    TableConsolidatedBudget, \
    TableBudgetAllocationsData, \
    TableAllocationAccounts
from utils.db_connect import db_sessionmaker
import utils.misc_functions

def import_budget_data_to_database(filepath, overwrite_data=False):
    ''' Imports a *.csv flatfile of Budget data into the database

    :param filepath: Absolute filepath of the *.csv file to be updated
    :param overwrite_data: User-specified permission to overwrite old data
    :return:
    '''
    # ToDo: Check if period is locked

    # Get import flatfile
    file_as_lists = utils.misc_functions.open_csv_file_as_list(filepath)

    # Confirm whether old data exists and if so, if it should be overwritten
    import_tag = file_as_lists[0][7]
    if check_label_exists_in_database(label=import_tag):
        if overwrite_data:
            delete_existing_budget_data_by_label(table=TableFinModelExtract, label=import_tag)
        else:
            raise error_objects.BudgetDataExistsError("Data already exists for tag '{}', import process aborted.\n "
                                                      "Re-run process selecting --overwrite=True to overwrite data."
                                                      .format(import_tag))

    # Import the data to the database
    session = db_sessionmaker()
    for row in file_as_lists:
        new_row = TableFinModelExtract(
                                        TimeStamp = convert_string_to_datetime(row[1]),
                                        Period = convert_string_to_datetime(row[2]),
                                        CompanyCode = row[3],
                                        CostCentreCode = row[4],
                                        GLCode = row[5],
                                        Value = row[6],
                                        Label = row[7],
                                        Comments = row[8]
                                        )
        session.add(new_row)

    session.commit()
    session.close()

def check_label_exists_in_database(label):
    ''' Confirms whether a tag already exists in the database

    :param label:
    :return:
    '''

    session = db_sessionmaker()
    results = session.query(TableFinModelExtract).filter_by(Label=label).all()
    session.close()
    if results:
        return True
    else:
        return False

def convert_string_to_datetime(input_date):
    ''' Converts a date represented by a string into a datetime.datetime object

    :param input_date: Date represented by a string
    :return: datetime.datetime object
    '''

    day_first=True

    # Check whether the date follows a yyyy-mm-dd or dd/mm/yyyy format
    # ToDo: This is a workaround - need a better solution

    test_input = input_date[:]
    if " " in test_input:
        test_input = test_input.split(" ")[0]

    if "-" in test_input:
        date_list = test_input.split("-")
        # Crude check whether the year is first or last
        if (int(date_list[0]) > 12) and (int(date_list[2]) < 2000):
            day_first = False
    elif "/" in test_input:
        date_list = test_input.split("/")
        if (int(date_list[0]) > 12) and (int(date_list[2]) < 2000):
            pass

    converted_datetime = parser.parse(input_date, dayfirst=day_first)

    return converted_datetime

def delete_existing_budget_data_by_label(table, label):
    ''' Deletes data in the tbl_DATA_finmodelextract by tag

    :param table: Database table data is to be deleted from
    :param label: Tag attached to the data by the user
    :return:
    '''

    session = db_sessionmaker()
    session.query(table).filter_by(Label=label).delete()
    session.commit()
    session.close()

def create_consolidated_budget_data(label):
    ''' Creates a consolidated table of Budget data, including both direct and allocated costs

    :return:
    '''

    session = db_sessionmaker()

    # Get unallocated data
    unalloc_data = session.query(TableFinModelExtract,
                           TableCompanies,
                           TableChartOfAccounts,
                           TableNodeHierarchy,
                           TableCostCentres)\
        .filter(TableFinModelExtract.Label==label)\
        .filter(TableFinModelExtract.CompanyCode==TableCompanies.CompanyCode)\
        .filter(TableFinModelExtract.CostCentreCode==TableCostCentres.CostCentreCode)\
        .filter(TableFinModelExtract.GLCode==TableChartOfAccounts.GLCode)\
        .filter(TableChartOfAccounts.L3Code==TableNodeHierarchy.L3Code)\
        .all()

    # To reference a table more than once (sender, receiver cost centres) we need to alias the table
    cc_alias_sending = aliased(TableCostCentres)
    cc_alias_receiving = aliased(TableCostCentres)
    comp_alias_sending = aliased(TableCompanies)
    comp_alias_receiving = aliased(TableCompanies)

    # Get allocated data
    alloc_qry = session.query(TableBudgetAllocationsData,
                              comp_alias_sending,
                              comp_alias_receiving,
                              cc_alias_sending,
                              cc_alias_receiving,
                              TableAllocationAccounts)\
        .filter(TableBudgetAllocationsData.Label==label)\
        .filter(TableBudgetAllocationsData.SendingCompany==comp_alias_sending.CompanyCode)\
        .filter(TableBudgetAllocationsData.ReceivingCompany==comp_alias_receiving.CompanyCode)\
        .filter(TableBudgetAllocationsData.SendingCostCentre==cc_alias_sending.CostCentreCode)\
        .filter(TableBudgetAllocationsData.ReceivingCostCentre==cc_alias_receiving.CostCentreCode)\
        .filter(TableBudgetAllocationsData.GLAccount == TableAllocationAccounts.GLCode)\
        .all()

    session.close()

    # Create row objects for the allocated and unallocated data
    consol_table_rows = []
    time_stamp = datetime.datetime.now()

    for budget, comp, coa, node, cc in unalloc_data:

        consol_row = TableConsolidatedBudget(
                                        Period = budget.Period,
                                        CompanyCode = budget.CompanyCode,
                                        CompanyName = comp.CompanyName,
                                        PartnerCompanyCode = None,
                                        PartnerCompanyName = None,
                                        CostCentreCode = budget.CostCentreCode,
                                        CostCentreName = cc.CostCentreName,
                                        PartnerCostCentreCode = None,
                                        PartnerCostCentreName = None,
                                        FinancialStatement = node.L0Name,
                                        GLAccountCode = budget.GLCode,
                                        GLAccountName = coa.GLName,
                                        L1Code = node.L1Code,
                                        L1Name = node.L1Name,
                                        L2Code = node.L2Code,
                                        L2Name = node.L2Name,
                                        L3Code = node.L3Code,
                                        L3Name = node.L3Name,
                                        CostHierarchyNumber = None,
                                        Value = budget.Value,
                                        TimeStamp = time_stamp,
                                        Label = budget.Label
                                        )
        consol_table_rows.append(consol_row)

    # Append the data from the cost allocations table
    for data, comp_send, comp_rec, cc_send, cc_rec, alloc_accounts in alloc_qry:
        alloc_row = TableConsolidatedBudget(
                                            Period = data.Period,
                                            CompanyCode = comp_rec.CompanyCode,
                                            CompanyName = comp_rec.CompanyName,
                                            PartnerCompanyCode = comp_send.CompanyCode,
                                            PartnerCompanyName = comp_send.CompanyName,
                                            CostCentreCode = cc_rec.CostCentreCode,
                                            CostCentreName = cc_rec.CostCentreName,
                                            PartnerCostCentreCode = cc_send.CostCentreCode,
                                            PartnerCostCentreName = cc_send.CostCentreName,
                                            FinancialStatement = alloc_accounts.L0Name,
                                            GLAccountCode = alloc_accounts.GLCode,
                                            GLAccountName = alloc_accounts.GLName,
                                            L1Code = alloc_accounts.L1Code,
                                            L1Name = alloc_accounts.L1Name,
                                            L2Code = alloc_accounts.L2Code,
                                            L2Name = alloc_accounts.L2Name,
                                            L3Code = alloc_accounts.L3Code,
                                            L3Name = alloc_accounts.L3Name,
                                            CostHierarchyNumber = data.CostHierarchy,
                                            Value = data.Value,
                                            TimeStamp = time_stamp,
                                            Label = data.Label
                                            )
        consol_table_rows.append(alloc_row)

    # Check that the label is the same in each row
    all_labels = list(set([row.Label for row in consol_table_rows]))
    assert len(all_labels) == 1, "Labels in consolidated budget data exceed len()=1:\n{}".format(all_labels)

    # Delete the old data
    delete_existing_budget_data_by_label(table=TableConsolidatedBudget, label=all_labels[0])

    # Add the new data
    session = db_sessionmaker()
    for row in consol_table_rows:
        session. add(row)
    session.commit()
    session.close()


### ToDo: Headcount calcs in the actuals import misses new starters from current period
