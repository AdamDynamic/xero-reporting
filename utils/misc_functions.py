'''
Contains miscellaneous io operations not captured by the other modules
'''

import csv
import datetime

from customobjects.database_objects import TablePeriods
from db_connect import db_sessionmaker


def import_csv_to_dict(file_location):
    ''' Opens and imports a CSV file and outputs the data as a list of dictionaries

    :param file_location: The relative location of the csv file to be imported
    :return: A list of dictionaries, one per row of the csv file
    '''

    with open(file_location, 'rb') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return rows

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

    session = db_sessionmaker()
    date_to_check = datetime.datetime(year=year, month=month, day=1)
    lock_check = session.query(TablePeriods).filter(TablePeriods.Period==date_to_check).one()
    session.close()
    return lock_check.IsLocked