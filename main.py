#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Command Line Interface for the management reporting database and associated functions
'''

import os
import requests

import click

import utils.data_integrity
from customobjects import error_objects, database_objects
from management_accounting.allocations import allocate_indirect_cost_for_period
from management_accounting.data_import import create_internal_financial_statements, create_consolidated_financial_statements
import references as r
from utils.console_output import util_output, display_status_table
import utils.misc_functions
from utils.xero_connect import pull_xero_data_to_database

@click.group()
def fin_reporting():
    pass

@fin_reporting.command(help="Retrieves financial data from Xero")
@click.option('--year', type=int, help="The year of the period to get Xero data for")
@click.option('--month', type=int, help="The month of the period to get Xero data for")
def get_xero_data(year, month):
    ''' Pulls data from the company Xero instance and imports it into the reporting
        database using standardised master data

    :param year:
    :param month:
    :return:
    '''

    try:
        util_output("Retrieving Xero data for period {}.{}...".format(year, month))
        pull_xero_data_to_database(year=year, month=month)
        util_output("Pull of Xero data for period {}.{} is complete".format(year, month))

    except (error_objects.PeriodIsLockedError,
            error_objects.PeriodNotFoundError,
            error_objects.MasterDataIncompleteError,
            error_objects.BalanceSheetImbalanceError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Import of Xero data aborted")

    except requests.exceptions.ConnectionError:
        util_output("ERROR: Unable to establish connection to Xero API. Check network connectivity.")
        util_output("ERROR: Import of Xero data aborted")


@fin_reporting.command(help="Converts Xero data into standard Clearmatics format")
@click.option('--year', type=int, help="The year of the period of Xero data to convert")
@click.option('--month', type=int, help="The month of the period of Xero data to convert")
def convert_xero_data(year, month):
    ''' Converts imported Xero data into the standardised internal format

    :param year: Year to convert (Integer)
    :param month: Month of the year to convert (Integer)
    :return:
    '''

    try:
        util_output("Converting Xero data for period {}.{}".format(year, month))
        create_internal_financial_statements(year=year, month=month)
        util_output("Conversion of Xero data complete")

    except (error_objects.PeriodIsLockedError,
            error_objects.PeriodNotFoundError,
            error_objects.TableEmptyForPeriodError,
            error_objects.MasterDataIncompleteError,
            error_objects.BalanceSheetImbalanceError,
            error_objects.CashFlowCalculationError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Conversion of Xero data is aborted")


@fin_reporting.command(help="Runs indirect cost allocations")
@click.option('--year', type=int, help="The year of the period to run allocations on")
@click.option('--month', type=int, help="The month of the period to run allocations on")
def run_allocations(year, month):
    ''' Runs the allocation process on extracted Xero data following its conversion to
        standardised company master data

    :param year: Year of the period to run allocations on (Integer)
    :param month: Month of the period to run allocations on (Integer)
    :return:
    '''

    try:
        util_output("Starting allocations process for period {}.{}...".format(year,month))
        allocate_indirect_cost_for_period(year=year, month=month)
        util_output("Allocation process for period {}.{} is complete".format(year, month))

    except (error_objects.PeriodIsLockedError,
            error_objects.PeriodNotFoundError,
            error_objects.TableEmptyForPeriodError,
            error_objects.MasterDataIncompleteError,
            error_objects.BalanceSheetImbalanceError,
            error_objects.CashFlowCalculationError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of cost allocations aborted")


@fin_reporting.command(help="Creates the consolidated reporting table")
@click.option('--year', type=int, help="The year of the period to create an output table for")
@click.option('--month', type=int, help="The month of the period to create an output table for")
def create_consolidated_table(year,month):
    ''' Creates a single, consolidated reporting table that includes allocation data and
        standardised company master data mappings

    :param kwargs:
    :return:
    '''
    try:
        util_output("Creating consolidated Income Statement for period {}.{}...".format(year, month))
        create_consolidated_financial_statements(year=year, month=month)
        util_output("Creation of consolidated Income Statement complete")

    except (error_objects.PeriodIsLockedError,
            error_objects.PeriodNotFoundError,
            error_objects.TableEmptyForPeriodError,
            error_objects.MasterDataIncompleteError,
            error_objects.BalanceSheetImbalanceError,
            error_objects.CashFlowCalculationError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of consolidated table aborted")


@fin_reporting.command(help="Locks/unlocks a given period in the database")
@click.option('--year', type=int, help="The year of the period in the database to lock")
@click.option('--month', type=int, help="The month of the period in the database to lock")
@click.option('--locked', type=bool, help="True/False of whether to lock the period")
def set_period_lock(year, month, locked):
    ''' Locks/unlocks a given period in the reporting database to prevent data being overwritten

    :param year:
    :param month:
    :param locked:
    :return:
    '''

    try:
        utils.data_integrity.check_period_exists(year=year, month=month)

    except error_objects.PeriodNotFoundError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Setting of period lock aborted")

    else:
        # Execute the lock/unlocking process only if the period is valid and exists in the database

        if not locked in [True, False]:
            util_output("ERROR: User input '{}' not recognised: options are 'True' or 'False'".format(locked))
        else:
            check_status = False
            # Perform additional check only if the user wants to unlock a period (i.e. ok to lock without checking)
            if locked == False:
                check_input = raw_input("Please confirm you want to unlock period {}.{} (Y/N):".format(year, month))
                if check_input in ['y','Y']:
                    check_status=True
            else:
                check_status=True

            if check_status:
                utils.misc_functions.set_period_lock_status(year=year, month=month, status=locked)
                util_output("Reporting period {}.{} is {}".format(year, month, ("LOCKED" if locked else "UNLOCKED")))
            else:
                util_output("Locking process aborted for period {}.{}".format(year, month))


@fin_reporting.command(help="Outputs the consolidated tables to csv")
@click.option('--folder', default=r.DEFAULT_OUTPUT_FOLDERPATH, help="Folder location to output files to")
def output_to_csv(folder):
    ''' Outputs the consolidated income statement to a csv file to the file position specified by the user

    :param folder:
    :return:
    '''

    # If no folder is specified by the user, default to the current directory with default output directory
    if folder == r.DEFAULT_OUTPUT_FOLDERPATH:

        current_file_location = os.path.realpath(__file__)
        current_dir_location = os.path.dirname(current_file_location)
        output_dir = utils.misc_functions.convert_dir_path_to_standard_format(folder_path=current_dir_location)
        output_dir += r.DEFAULT_OUTPUT_FOLDERNAME
        folder = utils.misc_functions.convert_dir_path_to_standard_format(folder_path=output_dir)
        utils.misc_functions.open_or_create_folder(folder)
        util_output("Outputting table {} to default file location:\n{}..."
                    .format(database_objects.TableConsolidatedFinStatements.__tablename__, folder))
    else:

        # Standardise the folder passed to the function by the user
        folder = utils.misc_functions.convert_dir_path_to_standard_format(folder_path=folder)
        folder += r.DEFAULT_OUTPUT_FOLDERNAME
        folder = utils.misc_functions.convert_dir_path_to_standard_format(folder_path=folder)

        util_output("Outputting table {} to user-specified file location:\n{}..."
                    .format(database_objects.TableConsolidatedFinStatements.__tablename__, folder))

    # If the inputted folder is correctly formatted and exists, output the table
    if utils.data_integrity.check_directory_exists(folder):
        utils.misc_functions.output_table_to_csv(table=database_objects.TableConsolidatedFinStatements,
                                                 output_directory=folder)
        util_output("Table output complete.")
    else:
        util_output("ERROR: Directory {} does not exist".format(folder))
        util_output("ERROR: Output of table {} aborted".format(database_objects.
                                                               TableConsolidatedFinStatements.__tablename__))


@fin_reporting.command(help="Displays the current status of the reporting data in the database")
def status():
    ''' Displays the summary status table in the console that displays which the status of the financial data
        in each period.

    :return:
    '''
    display_status_table()


if __name__ == '__main__':
    fin_reporting()