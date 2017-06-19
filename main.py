#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Command Line Interface for the management reporting database and associated functions
'''

import requests

import click

from customobjects import error_objects
from management_accounting.allocations import allocate_indirect_cost_for_period
from management_accounting.data_import import create_internal_profit_and_loss, create_consolidated_income_statement
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

    except error_objects.PeriodIsLockedError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Import of Xero data aborted")

    except error_objects.PeriodNotFoundError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Import of Xero data aborted")

    except requests.exceptions.ConnectionError:
        util_output("ERROR: Unable to establish connection to Xero API. Check network connectivity.")
        util_output("ERROR: Import of Xero data aborted")


@fin_reporting.command(help="Converts Xero data into standard Clearmatics format")
@click.option('--year', type=int, help="The year of the period of Xero data to convert")
@click.option('--month', type=int, help="The month of the period of Xero data to convert")
def convert_xero_data(year, month):
    '''

    :param year:
    :param month:
    :return:
    '''

    try:
        util_output("Converting Xero data for period {}.{}".format(year, month))
        create_internal_profit_and_loss(year=year, month=month)
        util_output("Conversion of Xero data complete")

    except error_objects.PeriodIsLockedError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Conversion of Xero data is aborted")

    except error_objects.PeriodNotFoundError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Conversion of Xero data is aborted")

    except error_objects.TableEmptyForPeriodError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Conversion of Xero data is aborted")

@fin_reporting.command(help="Runs indirect cost allocations")
@click.option('--year', type=int, help="The year of the period to run allocations on")
@click.option('--month', type=int, help="The month of the period to run allocations on")
def run_allocations(year, month):
    ''' Runs the allocation process on extracted Xero data following its conversion to
        standardised company master data

    :param year:
    :param month:
    :return:
    '''

    try:
        util_output("Starting allocations process for period {}.{}...".format(year,month))
        allocate_indirect_cost_for_period(year=year, month=month)
        util_output("Allocation process for period {}.{} is complete".format(year, month))

    except error_objects.PeriodIsLockedError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of cost allocations aborted")

    except error_objects.PeriodNotFoundError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of cost allocations aborted")

    except error_objects.TableEmptyForPeriodError, e:
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
        create_consolidated_income_statement(year=year, month=month)
        util_output("Creation of consolidated Income Statement complete")

    except error_objects.PeriodIsLockedError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of consolidated table aborted")

    except error_objects.PeriodNotFoundError, e:
        util_output("ERROR: {}".format(e.message))
        util_output("ERROR: Creation of consolidated table aborted")

    except error_objects.TableEmptyForPeriodError, e:
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
        utils.misc_functions.check_period_exists(year=year, month=month)

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

@fin_reporting.command(help="Displays the current status of the reporting data in the database")
def status():
    ''' Displays the summary status table in the console that displays which the status of the financial data
        in each period.

    :return:
    '''
    display_status_table()


if __name__ == '__main__':
    fin_reporting()