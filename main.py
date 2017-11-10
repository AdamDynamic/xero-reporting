#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Command Line Interface for the management reporting database and associated functions
'''

import click
import requests

import utils.data_integrity
import utils.misc_functions
from budget import budget_import
from customobjects import error_objects, database_objects
from management_accounting.allocations import allocate_actuals_data, allocate_budget_data
from management_accounting.data_import import create_internal_financial_statements, create_consolidated_financial_statements
from utils.console_output import util_output, display_status_table
from utils.misc_functions import user_confirm_action_on_period
from utils.xero_connect import pull_xero_data_to_database

@click.group()
def fin_reporting():
    pass

@fin_reporting.command(help="Locks/unlocks a given period in the database")
@click.option('--year', type=int, help="The year of the period in the database to lock")
@click.option('--month', type=int, help="The month of the period in the database to lock")
@click.option('--locked', type=bool, help="True/False of whether to lock the period")
def actuals_lock_period(year, month, locked):
    ''' Locks/unlocks a given period in the reporting database to prevent data being overwritten

    :param year: Year of the actuals dataset to lock
    :param month: Month of the actuals dataset to lock
    :param locked: True/False whether the period should be locked (True) or unlocked (False)
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
            check_status = user_confirm_action_on_period(action=('LOCK' if locked else 'UNLOCK'),
                                                         dataset=str(year) + "." + str(month))

            if check_status:
                utils.misc_functions.set_period_lock_status(year=year, month=month, status=locked)
                util_output("Reporting period {}.{} is {}".format(year, month, ("LOCKED" if locked else "UNLOCKED")))
            else:
                util_output("Locking process aborted for period {}.{}".format(year, month))


@fin_reporting.command(help="Published/unpublishes a given period in the database")
@click.option('--year', type=int, help="The year of the period in the database to publish")
@click.option('--month', type=int, help="The month of the period in the database to publish")
@click.option('--publish', type=bool, help="True/False of whether to publish the period")
def actuals_publish_period(year, month, publish):
    ''' Publishes/unpublishes (makes available to external reports) a given period in the reporting database
    to prevent data being exposed before it is considered ready by the user

    :param year: Year of the actuals dataset to publish
    :param month: Month of the actuals dataset to publish
    :param publish: True/False whether the period should be published (True) or unpublished (False)
    :return:
    '''

    try:
        utils.data_integrity.check_period_exists(year=year, month=month)

    except error_objects.PeriodNotFoundError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Setting of period publish status aborted")

    else:
        # Execute the publishing/unpublishing process only if the period is valid and exists in the database

        if not publish in [True, False]:
            util_output("ERROR: User input '{}' not recognised: options are 'True' or 'False'".format(publish))
        else:
            check_status = user_confirm_action_on_period(action=('PUBLISH' if publish else 'UNPUBLISH'),
                                                         dataset=str(year)+"."+str(month))
            if check_status:
                utils.misc_functions.set_period_published_status(year=year, month=month, status=publish)
                util_output("Reporting period {}.{} is {}".format(year, month, ("PUBLISHED" if publish else "UNPUBLISHED")))
            else:
                util_output("Publishing process aborted for period {}.{}".format(year, month))


@fin_reporting.command(help="Retrieves financial data from Xero")
@click.option('--year', type=int, help="The year of the period to get Xero data for")
@click.option('--month', type=int, help="The month of the period to get Xero data for")
def actuals_get_data(year, month):
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
            error_objects.BalanceSheetImbalanceError,
            error_objects.UnallocatedCostsNotNilError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Import of Xero data aborted")

    except requests.exceptions.ConnectionError:
        util_output("ERROR: Unable to establish connection to Xero API. Check network connectivity.")
        util_output("ERROR: Import of Xero data aborted")


@fin_reporting.command(help="Converts Xero data into standard Clearmatics format")
@click.option('--year', type=int, help="The year of the period of Xero data to convert")
@click.option('--month', type=int, help="The month of the period of Xero data to convert")
def actuals_convert_data(year, month):
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
def actuals_run_allocations(year, month):
    ''' Runs the allocation process on extracted Xero data following its conversion to
        standardised company master data

    :param year: Year of the period to run allocations on (Integer)
    :param month: Month of the period to run allocations on (Integer)
    :return:
    '''

    try:
        util_output("Starting allocations process for period {}.{}...".format(year,month))
        allocate_actuals_data(year=year, month=month)
        util_output("Allocation process for period {}.{} is complete".format(year, month))

    except (error_objects.PeriodIsLockedError,
            error_objects.PeriodNotFoundError,
            error_objects.TableEmptyForPeriodError,
            error_objects.MasterDataIncompleteError,
            error_objects.BalanceSheetImbalanceError,
            error_objects.CashFlowCalculationError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of cost allocations aborted")


@fin_reporting.command(help="Creates the consolidated Financial Statements table")
@click.option('--year', type=int, help="The year of the period to create an output table for")
@click.option('--month', type=int, help="The month of the period to create an output table for")
def actuals_create_consol_table(year, month):
    ''' Creates a single, consolidated reporting table that includes allocation data and
        standardised company master data mappings

    :param kwargs:
    :return:
    '''
    try:
        util_output("Creating consolidated Financial Statements for period {}.{}...".format(year, month))
        create_consolidated_financial_statements(year=year, month=month)
        util_output("Creation of consolidated Financial Statements complete")

    except (error_objects.PeriodIsLockedError,
            error_objects.PeriodNotFoundError,
            error_objects.TableEmptyForPeriodError,
            error_objects.MasterDataIncompleteError,
            error_objects.BalanceSheetImbalanceError,
            error_objects.CashFlowCalculationError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of consolidated Financial Statements aborted")


@fin_reporting.command(help="Imports a flatfile of Budget data")
@click.option('--overwrite', default=False, help="Overwrites previously imported data")
def budget_get_data(overwrite):
    ''' Imports budget data in *.csv flatfile format

    :return:
    '''

    util_output("Select file for import:")
    file_to_import = utils.misc_functions.get_filename_from_gui()
    if file_to_import:
        try:
            util_output("Importing file {}...".format(file_to_import))
            budget_import.import_budget_data_to_database(filepath=file_to_import,overwrite_data=overwrite)
        except error_objects.BudgetDataExistsError, e:
            util_output("ERROR: {}".format(e.message))
            util_output("ERROR: Import of Budget data is aborted")
        else:
            util_output("File import successful.")
    else:
        util_output("No file selected by user, import process aborted.")


@fin_reporting.command(help="Runs indirect cost allocations on budget data")
@click.option('--label', help="Label of budget data to allocate")
@click.option('--max_year', type=int, default=9999, help="The last year of the data to run allocations on")
@click.option('--max_month', type=int, default=13, help="The last month of the data to run allocations on")
def budget_run_allocations(label, max_year=9999, max_month=13):
    ''' Runs the allocation process on extracted Xero data following its conversion to
        standardised company master data

    :param year: Year of the period to run allocations on (Integer)
    :param month: Month of the period to run allocations on (Integer)
    :return:
    '''

    try:
        # ToDo: add check that the input dates are valid
        util_output("Starting budget allocation process for {} up to period {}.{}...".format(label, max_year, max_month))
        allocate_budget_data(label=label, max_year=max_year, max_month=max_month)
        util_output("Budget allocation process for dataset {} is complete".format(label))

    except (error_objects.PeriodIsLockedError,
            error_objects.PeriodNotFoundError,
            error_objects.TableEmptyForPeriodError,
            error_objects.MasterDataIncompleteError,
            error_objects.BalanceSheetImbalanceError,
            error_objects.CashFlowCalculationError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of cost allocations aborted")


@fin_reporting.command(help="Creates the consolidated Budget Financial Statements table")
@click.option('--label', help="Label of budget data to consolidate")
def budget_create_consol_table(label):
    ''' Creates a single, consolidated reporting table that includes allocation data and
        standardised company master data mappings

    :param kwargs:
    :return:
    '''
    try:
        util_output("Creating consolidated Budget Financial Statements for {}...".format(label))
        budget_import.create_consolidated_budget_data(label=label)
        util_output("Creation of consolidated Budget Financial Statements complete")

    except (error_objects.PeriodIsLockedError,
            error_objects.PeriodNotFoundError,
            error_objects.TableEmptyForPeriodError,
            error_objects.MasterDataIncompleteError,
            error_objects.BalanceSheetImbalanceError,
            error_objects.CashFlowCalculationError), e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of consolidated Budget Financial Statements aborted")


@fin_reporting.command(help="Outputs the consolidated tables to csv")
def output_to_csv():
    ''' Outputs the consolidated income statement to a csv file to the file position specified by the user

    :param folder:
    :return:
    '''

    # Prompt the user to select the folder to output the data to:
    util_output("Select the folder to output files to:")
    folder = utils.misc_functions.get_directoryname_from_gui()
    if folder:

        folder = utils.misc_functions.convert_dir_path_to_standard_format(folder_path=folder)

        if utils.data_integrity.check_directory_exists(folder):
            util_output("Outputting table {}...".format(database_objects.TableConsolidatedFinStatements.__tablename__))
            utils.misc_functions.output_table_to_csv(table=database_objects.TableConsolidatedFinStatements,
                                                     output_directory=folder)
            util_output("Output of table {} complete.".format(database_objects.TableConsolidatedFinStatements.__tablename__))

            util_output("Outputting table {}...".format(database_objects.TableConsolidatedBudget.__tablename__))
            utils.misc_functions.output_table_to_csv(table=database_objects.TableConsolidatedBudget,
                                                     output_directory=folder)
            util_output(
                "Output of table {} complete.".format(database_objects.TableConsolidatedBudget.__tablename__))

            util_output("Table output complete.")
        else:
            util_output("ERROR: Directory {} does not exist".format(folder))
            util_output("ERROR: Output of tables {} and {} aborted"
                        .format(database_objects.TableConsolidatedFinStatements.__tablename__,
                                database_objects.TableConsolidatedBudget.__tablename__))

    else:
        util_output("No folder selected by user. Output process aborted.")


@fin_reporting.command(help="Displays the current status of the reporting data in the database")
def status():
    ''' Displays the summary status table in the console that displays which the status of the financial data
        in each period.

    :return:
    '''
    display_status_table()


if __name__ == '__main__':
    fin_reporting()