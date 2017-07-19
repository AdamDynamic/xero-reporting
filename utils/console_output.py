#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains helper and utility functions used to output messages to the command window as part of the command line interface
'''

import datetime
import os
import sys

import click
from tabulate import tabulate
from sqlalchemy import func, asc

from customobjects.database_objects import TablePeriods, \
    TableXeroExtract, \
    TableFinancialStatements, \
    TableConsolidatedFinStatements, \
    TableAllocationsData
import customobjects.error_objects as error_objects
from utils.data_integrity import get_all_bs_nodes_unmapped_for_cashflow
import utils.data_integrity
from utils.db_connect import db_sessionmaker
import utils.misc_functions
import references as r

def get_command_window_width():
    ''' Returns the width (number of columns) of the current command window as an integer

    :return: The number of columns in the current command window as an integer
    '''
    cols = 0
    try:
        rows, cols = os.popen('stty size', 'r').read().split()
    except ValueError:
        cols = 100   # If there is no window to measure (i.e. running from IDE) then a valueerror is created
    finally:
        return int(cols)

def progress_bar(iteration, total, prefix="", suffix="", decimals=1, number_of_cols=0):
    ''' Displays a fixed-position progress bar in the command window

    :param iteration: The current iteration of the process
    :param total: The total number of expected iterations in the process
    :param prefix: The prefix to be printed before the process bar in the command window
    :param suffix: The suffix to be printed after the process bar in the command window
    :param decimals: The number of decimal places to add to the percentage displayed
    :param number_of_cols: The number of columns across which to display the progress bar
    :return:
    '''

    # If the window-width is set as the default of 0, fit to the width of the current command window
    if number_of_cols==0:
        number_of_cols=get_command_window_width()

    # Create the bar graphic
    format_string = "{0:."+str(decimals) + "f}"
    percent = format_string.format(100*(iteration/(total*1.0))).zfill(4+decimals)

    barlength = number_of_cols - len(prefix) - len(suffix) - (10 + decimals) # Padding so the final bar doesn't wrap onto the next line

    filled_length = int(round((barlength*iteration)/(total*1.0)))
    bar = '#'*filled_length+"-"*(barlength-filled_length)

    sys.stdout.write('\r{} |{}| {}{} {}'.format(prefix,bar,percent,'%',suffix))
    if iteration==total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def util_output(message):
    ''' Outputs to the console screen and logs as an INFO message via the logging module.

    :param message: The string to be displayed and logged
    :return:
    '''

    timestamp = datetime.datetime.now()
    enhanced_message = timestamp.strftime("%I:%M:%S") + ": " + str(message)
    click.echo(enhanced_message)

def process_timestamp_validation_check(xero_date, pnl_date, alloc_date, consol_date):
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

def display_status_table():
    ''' Outputs to the console a summary table of the status of each reporting period

    :return:
    '''

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

    # Convert to .date() as the data is extracted from the period_qry as datetime.date() objects
    xero_dates = [row.Period.date() for row in xero_qry if row.count != 0]
    pnl_dates = [row.Period.date() for row in pnl_qry if row.count != 0]
    alloc_dates = [row.Period.date() for row in alloc_qry if row.count != 0]
    consol_dates = [row.Period.date() for row in consol_qry if row.count != 0]

    table_headers = ["Period", "IsLocked", "1) XeroData", "2) Converted", "3) Allocations", "4) Consol", "TimestampCheck"]

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

        validation_check = process_timestamp_validation_check(xero_date=xero_timestamp,
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
                      ('Pass' if validation_check==5 else 'Run From Step {}'.format(validation_check))
                      ]
        table_rows.append(table_row)

    session.close()

    # Output the table to the console
    print "\n" + tabulate(tabular_data=table_rows, headers=table_headers, numalign="right") + "\n"

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
