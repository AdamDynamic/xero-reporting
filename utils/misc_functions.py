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
from customobjects.database_objects import TablePeriods, TableXeroExtract, TableChartOfAccounts
from customobjects import error_objects
from utils.db_connect import db_sessionmaker

#
# def import_csv_to_dict(file_location):
#     ''' Opens and imports a CSV file and outputs the data as a list of dictionaries
#
#     :param file_location: The relative location of the csv file to be imported
#     :return: A list of dictionaries, one per row of the csv file
#     '''
#
#     with open(file_location, 'rb') as f:
#         reader = csv.DictReader(f)
#         rows = list(reader)
#         return rows

def get_datetime_of_last_day_of_month(year=None, month=None):
    ''' Returns a datetime object of the last day of the month

    :param year:
    :param month:
    :return:
    '''
    # ToDo: Refactor and include in xero_connect module
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