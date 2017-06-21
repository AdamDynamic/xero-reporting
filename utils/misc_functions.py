#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains miscellaneous io operations not captured by the other modules
'''

import csv
import datetime

import sqlalchemy
import sqlalchemy.orm

import references as r
from customobjects.database_objects import TablePeriods, TableXeroExtract, TableChartOfAccounts, TableConsolidatedIncomeStatement
from customobjects import error_objects
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

def check_table_has_records_for_period(year,month,table):
    ''' Checks whether a table contains a non-zero number of records for a given period

    :param year:
    :param month:
    :param table:
    :return:
    '''

    check_period_exists(year=year,month=month)
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

def output_table_to_csv(table, file_location):
    ''' Outputs a database table to a *.csv file, saved to a location specified by the user

    :param table: The table object to be outputed
    :param file_location: Where the user would like the *.csv file saved
    :return:
    '''

    timestamp = datetime.datetime.now().strftime("yyyymmdd-hhmmss") # ToDo: Doesn't work

    file_name = file_location + table.__name__ + timestamp + ".csv"  # ToDo: Check concatenation of /'s etc in filename
    output_file = open(file_name, 'wb')
    writer = csv.writer(output_file)

    session = db_sessionmaker()
    records = session.query(table).all()
    print records
    # ToDo: Need to write header row first
    [writer.writerow([getattr(curr, column.name) for column in table.__mapper__.columns]) for curr in records]
    session.close()
    output_file.close()

    # ToDo: Only create file if the process is run successfully end-to-end

file_location = '/home/adam/Desktop/'
output_table_to_csv(table=TableConsolidatedIncomeStatement, file_location=file_location)
