#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains helper and utility functions used to output messages to the command window as part of the command line interface
'''

import datetime

import click
from tabulate import tabulate
from sqlalchemy import func, asc

from customobjects.database_objects import \
    TablePeriods, \
    TableXeroExtract, \
    TableFinancialStatements, \
    TableConsolidatedFinStatements, \
    TableAllocationsData, \
    TableFinModelExtract, \
    TableBudgetAllocationsData, \
    TableConsolidatedBudget
import customobjects.error_objects as error_objects
from utils.data_integrity import get_all_bs_nodes_unmapped_for_cashflow
import utils.data_integrity
from utils.db_connect import db_sessionmaker
import utils.misc_functions
import references as r

def util_output(message):
    ''' Outputs to the console screen and logs as an INFO message via the logging module.

    :param message: The string to be displayed and logged
    :return:
    '''

    timestamp = datetime.datetime.now()
    enhanced_message = timestamp.strftime("%I:%M:%S") + ": " + str(message)
    click.echo(enhanced_message)

def first_datetime_not_ascending(list_of_timestamps):
    ''' Returns the index of the first datetime that is later than the following datetime object in the list

    :param list_of_timestamps: List of timestamp objects
    :return: The list number of the first datetime that is earlier than the previous index number
    '''

    for time_stamp in list_of_timestamps:

        index_position = list_of_timestamps.index(time_stamp)

        if not time_stamp: # If there is no timestamp
            return index_position
        elif index_position==0: # Ignore the first item on the list
            pass
        elif list_of_timestamps[index_position-1] >= list_of_timestamps[index_position]: # Check later than the previous timestamp
            return index_position

    return len(list_of_timestamps) # If all the tests are passed

def run_actuals_from_step_number(xero_date, pnl_date, alloc_date, consol_date):
    ''' Confirms that the timestamps relating to the various processes in the end-to-end chain have been run
        in the correct order and that upstream data is current

    :param xero_date:
    :param pnl_date:
    :param alloc_date:
    :param consol_date:
    :return: The step number where the upstream timestamp is prior to the downstream timestamp
    '''

    # Unpack the dates passed to the functions as lists
    try:
        xero_date = xero_date[0]
    except IndexError:
        return 1

    try:
        pnl_date = pnl_date[0]
    except IndexError:
        return 2

    try:
        alloc_date = alloc_date[0]
    except IndexError:
        return 3

    try:
        consol_date = consol_date[0]
    except IndexError:
        return 4

    # The processes need to be run in order so that the data included in upstream processes are up to date
    # The risk is otherwise that a change could be made to Xero data but that change wouldn't be reflected
    # in allocations for example.
    if xero_date > pnl_date:
        return 2
    elif pnl_date > alloc_date:
        return 3
    elif alloc_date > consol_date:
        return 4
    else:
        return 5

def get_budget_status_table():
    ''' Returns a console table showing the status of imported Budget data

    :return:
    '''

    # 1) Create a list of all labels available in the import table
    session = db_sessionmaker()
    labels_qry = session.query(TableFinModelExtract.Label, TableFinModelExtract.TimeStamp, TableFinModelExtract.Comments)\
        .order_by(asc(TableFinModelExtract.TimeStamp))\
        .all()
    alloc_qry = session.query(TableBudgetAllocationsData.Label, TableBudgetAllocationsData.DateAllocationsRun)\
        .all()
    consol_qry = session.query(TableConsolidatedBudget.Label, TableConsolidatedBudget.TimeStamp).all()

    session.close()

    # 2) Remove duplicates
    labels_qry = list(set(labels_qry))
    alloc_qry = list(set(alloc_qry))
    consol_qry = list(set(consol_qry))

    labels_allocated = [label[0] for label in alloc_qry]
    labels_consol = [label[0] for label in consol_qry]
    # ToDo: Include "IsPublished flag"
    table_headers = ["Label", "IsLocked", "1) IsAllocated", "2) Consol", "TimestampCheck", "Comment"]
    table_rows = []

    # 3) Create a table row for each label imported
    for label in labels_qry:

        time_allocated = [alloc[1] for alloc in alloc_qry if alloc[0]==label[0]]
        time_consol = [consol[1] for consol in consol_qry if consol[0]==label[0]]
        ordered_timestamps = [time_allocated[0], time_consol[0]]
        time_stamp_check = first_datetime_not_ascending(list_of_timestamps=ordered_timestamps)

        table_row = [label[0],
                     "N/A",
                     ('Calculated' if label[0] in labels_allocated else 'Not Calculated'),
                     ('Calculated' if label[0] in labels_consol else 'Not Calculated'),
                     'Pass' if time_stamp_check == 2 else 'Run From Step {}'.format(time_stamp_check+1),
                     label[2]]

        table_rows.append(table_row)

    return tabulate(tabular_data=table_rows, headers=table_headers, numalign="right") + "\n"

def get_actuals_status_table():
    ''' Creates a console window table showing the import status of the various periods of actuals available

    :return:
    '''

    # ToDo: Add column with time-stamp of last operation

    session = db_sessionmaker()

    # Get all periods in the database up to today's date (all data is historic)
    period_qry = session.query(TablePeriods)\
        .order_by(asc(TablePeriods.Period))\
        .filter(TablePeriods.Period >= r.MODEL_START_DATE)\
        .filter(TablePeriods.Period <= datetime.datetime.now())\
        .all()

    # Extract the count of each row to determine whether the data exists and get the timestamp data to assert that
    # the data in the latter stages is up-to-date and that more recent data hasn't been created up-stream

    # Count the number of xero rows for each date
    xero_qry = session.query(TableXeroExtract.Period,
                             func.count(TableXeroExtract.ID).label('count'),
                             func.max(TableXeroExtract.DateExtracted).label('timestamp'))\
        .group_by(TableXeroExtract.Period)\
        .all()

    # Count the number of rows of data converted to internal mappings
    pnl_qry = session.query(TableFinancialStatements.Period,
                            func.count(TableFinancialStatements.ID).label('count'),
                            func.max(TableFinancialStatements.TimeStamp).label('timestamp'))\
        .group_by(TableFinancialStatements.Period)\
        .all()

    # Count the number of rows of data of allocated indirect costs
    alloc_qry = session.query(TableAllocationsData.Period,
                              func.count(TableAllocationsData.ID).label('count'),
                              func.max(TableAllocationsData.DateAllocationsRun).label('timestamp'))\
        .group_by(TableAllocationsData.Period)\
        .all()

    # Count the number of rows of data transformed into the consolidated income statement
    consol_qry = session.query(TableConsolidatedFinStatements.Period,
                               func.count(TableConsolidatedFinStatements.ID).label('count'),
                               func.max(TableConsolidatedFinStatements.TimeStamp).label('timestamp'))\
        .group_by(TableConsolidatedFinStatements.Period)\
        .all()

    session.close()

    # Convert to .date() as the data is extracted from the period_qry as datetime.date() objects
    xero_dates = [row.Period.date() for row in xero_qry if row.count != 0]
    pnl_dates = [row.Period.date() for row in pnl_qry if row.count != 0]
    alloc_dates = [row.Period.date() for row in alloc_qry if row.count != 0]
    consol_dates = [row.Period.date() for row in consol_qry if row.count != 0]
    # ToDo: Include 'IsPublished' flag
    table_headers = ["Period", "IsLocked", "1) ActualsData", "2) Converted",
                     "3) Allocations", "4) Consol", "TimestampCheck"]

    # table_rows are lists of values that correspond to the headers in the list above
    table_rows = []

    for qry_row in period_qry:

        # Get the timestamps of each process to check the order has been run correctly
        # ToDo: Refactor this so that the results aren't returned as lists
        # Results are returned as lists to capture the instance where no results are returned (returns [])
        xero_timestamp = list(set([row.timestamp for row in xero_qry if row.Period.date()==qry_row.Period]))
        pnl_timestamp = list(set([row.timestamp for row in pnl_qry if row.Period.date()==qry_row.Period]))
        alloc_timestamp = list(set([row.timestamp for row in alloc_qry if row.Period.date()==qry_row.Period]))
        consol_timestamp = list(set([row.timestamp for row in consol_qry if row.Period.date()==qry_row.Period]))

        # Check that the time-stamps of each step are in the correct order
        step_number_complete = run_actuals_from_step_number(xero_date=xero_timestamp,
                                                        pnl_date=pnl_timestamp,
                                                        alloc_date=alloc_timestamp,
                                                        consol_date=consol_timestamp)

        # ToDo: Include "recalculate" requirement for instance where the TimeStampCheck shows an error
        table_row = [qry_row.Period,
                      ('True' if qry_row.IsLocked else 'False'),
                      ('Imported' if qry_row.Period in xero_dates else 'Not Imported'),
                      ('Imported' if qry_row.Period in pnl_dates else 'Not Imported'),
                      ('Calculated' if qry_row.Period in alloc_dates else 'Not Calculated'),
                      ('Calculated' if qry_row.Period in consol_dates else 'Not Calculated'),
                      ('Pass' if step_number_complete==5 else 'Run From Step {}'.format(step_number_complete))
                      ]
        table_rows.append(table_row)

        # ToDo: Add col with NPAT total for the period (sense-check)

    # Output the table to the console
    return tabulate(tabular_data=table_rows, headers=table_headers, numalign="right") + "\n"

def display_status_table():
    ''' Outputs to the console a summary table of the status of each reporting period

    :return:
    '''

    print "##### ACTUALS DATA #####"
    actuals_table = get_actuals_status_table()
    print "\n" + actuals_table

    # Check whether any accounts aren't mapped to the master coa account
    unmapped_accounts = list(set(utils.data_integrity.get_unmapped_xero_account_codes()))
    if unmapped_accounts:
        print "The following Xero accounts are unmapped in the chart of accounts:"
        for row in unmapped_accounts:
            print " " + str(row)

    unmapped_cashflow_nodes = get_all_bs_nodes_unmapped_for_cashflow()
    if unmapped_cashflow_nodes:
        print "The following Balance Sheet nodes are unmapped for cash flow calculations:"
        for row in unmapped_cashflow_nodes:
            print " " + str(row)

    try:
       utils.data_integrity.master_data_uniquesness_check()
    except error_objects.MasterDataIncompleteError, e:
        print e.message

    try:
        utils.data_integrity.balance_sheet_balances_check()
    except error_objects.BalanceSheetImbalanceError, e:
        print e.message

    try:
        utils.data_integrity.coa_L3_nodes_in_hierarchy()
    except error_objects.MasterDataIncompleteError, e:
        print e.message

    print "##### BUDGET DATA #####"

    budget_table = get_budget_status_table()
    print "\n" + budget_table

    try:
        utils.data_integrity.check_budget_accounts_in_coa()
    except error_objects.MasterDataIncompleteError, e:
        print e.message