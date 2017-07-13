#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains miscellaneous io operations not captured by the other modules
'''

import csv
import datetime
import errno
import os

from customobjects import error_objects
from customobjects.database_objects import \
    TablePeriods, \
    TableXeroExtract, \
    TableChartOfAccounts
from utils.data_integrity import check_period_exists, check_period_is_locked
from utils.db_connect import db_sessionmaker


def get_datetime_of_last_day_of_month(year, month):
    ''' Returns a datetime object of the last day of the month

    :param year:
    :param month:
    :return:
    '''

    last_day = None
    if month == 12:
        last_day = datetime.datetime(year=year + 1, month=1, day=1)
    else:
        last_day = datetime.datetime(year=year, month=month + 1, day=1)
    last_day = last_day + datetime.timedelta(days=-1)
    return last_day

def check_table_has_records_for_period(year,month,table):
    ''' Checks whether a table contains a non-zero number of records for a given period

    :param year:
    :param month:
    :param table:
    :return:
    '''

    check_period_exists(year=year, month=month)
    period_to_check = datetime.datetime(year=year, month=month, day=1)
    session = db_sessionmaker()
    result = session.query(table).filter(table.Period==period_to_check).all()
    session.close()
    if result == []:
        raise error_objects.TableEmptyForPeriodError("Table {} contains no records for period {}.{}".format(table.__tablename__, year, month))

def set_period_lock_status(year, month, status):
    ''' Sets whether a period is locked or unlocked

    :param year:
    :param month:
    :param status:
    :return:
    '''

    assert status in [True, False], "User input is invalid - only TRUE or FALSE are permitted inputs"

    period_to_update = datetime.datetime(year=year, month=month, day=1)
    check_period_exists(year=year, month=month)
    session=db_sessionmaker()
    # If it exists, set the lock status
    set_lock = session.query(TablePeriods).filter(TablePeriods.Period == period_to_update).update({"IsLocked":status})
    session.commit()
    session.close()

def get_unmapped_account_codes():
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

def delete_table_data_for_period(table, year, month):
    ''' Deletes all data in a given table object for a specific year and month

    :param table: Sqlalchemy ORM table object of table where data should be deleted from
    :param year: Year of the period to delete
    :param month: Month of the period to delete
    :return:
    '''

    # ToDo: Only works if the table has a field called 'Period' > need some way to check existence

    date_to_delete = datetime.datetime(year=year, month=month, day=1)
    check_period_is_locked(year=year, month=month)
    session = db_sessionmaker()
    session.query(table).filter(table.Period==date_to_delete).delete()
    session.commit()
    session.close()

def convert_dir_path_to_standard_format(folder_path):
    ''' Standardises the folder path passed to the function

    :param folder_path:
    :return:
    '''

    if folder_path[-1] != "/":
        folder_path += "/"
    return folder_path

def open_or_create_folder(dir_path):
    ''' If a directory doesn't already exist, that directory is created

    :param dir_path:
    :return:
    '''

    try:
        os.makedirs(dir_path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

def output_table_to_csv(table, output_directory):
    ''' Outputs a database table to a *.csv file, saved to a location specified by the user

    :param table: The table object to be outputed
    :param output_directory: Where the user would like the *.csv file saved
    :return:
    '''

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create the default output directory if it doesn't already exist
    output_directory = convert_dir_path_to_standard_format(folder_path=output_directory)
    file_name = output_directory + table.__name__ + "_" + timestamp + ".csv"

    # Get all records from the related table
    session = db_sessionmaker()
    records = session.query(table).all()
    session.close()

    # Output the records to a csv file
    output_file = open(file_name, 'wb')
    writer = csv.writer(output_file)
    writer.writerow(table.__table__.columns.keys())
    [writer.writerow([getattr(curr, column.name) for column in table.__mapper__.columns]) for curr in records]
    output_file.close()

