#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains miscellaneous io operations not captured by the other modules
'''

import csv
import datetime
import errno
import os

from Tkinter import Tk
from tkFileDialog import askopenfilename, askdirectory

from customobjects import error_objects
from customobjects.database_objects import \
    TablePeriods
from utils.console_output import util_output
from utils.data_integrity import check_period_exists, check_period_is_locked
from utils.db_connect import db_sessionmaker
import references as r


def convert_dir_path_to_standard_format(folder_path):
    ''' Standardises the folder path passed to the function

    :param folder_path:
    :return:
    '''

    if folder_path[-1] != "/":
        folder_path += "/"
    return folder_path

def delete_table_data_for_period(table, year, month):
    ''' Deletes all data in a given table object for a specific year and month

    :param table: Sqlalchemy ORM table object of table where data should be deleted from
    :param year: Year of the period to delete
    :param month: Month of the period to delete
    :return:
    '''

    date_to_delete = datetime.datetime(year=year, month=month, day=1)
    check_period_is_locked(year=year, month=month)
    try:
        session = db_sessionmaker()
        session.query(table).filter(table.Period==date_to_delete).delete()
    except AttributeError, e:
        raise error_objects.MasterDataIncompleteError(e.message
                                                      + "\n(relevant table must have column named 'Period' "
                                                        "for the function to work)")
    else:
        session.commit()
    finally:
        session.close()

def get_filename_from_gui():
    ''' Prompts the user to select a file using a GUI and returns the filepath

    Taken from https://stackoverflow.com/questions/3579568/choosing-a-file-in-python-with-simple-dialog

    :return: Filepath of the user-selected file
    '''

    Tk().withdraw()
    filepath = askopenfilename()
    return filepath

def get_directoryname_from_gui():
    ''' Prompts the user to select a directory using a GUI and returns the filepath

    :return: Filepath of the user-selected file
    '''

    Tk().withdraw()
    directory = askdirectory()
    return directory

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

def open_csv_file_as_list(filepath):
    ''' Opens a *.csv file and returns a nested list of the file

    :param filepath:
    :return:
    '''

    with open(filepath, 'rb') as f:
        reader = csv.reader(f)
        output = list(reader)
    return output

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
    set_lock = session.query(TablePeriods).filter(TablePeriods.Period == period_to_update)\
        .update({r.COL_PERIOD_ISLOCKED:status})
    session.commit()
    session.close()

def set_period_published_status(year, month, status):
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
    set_lock = session.query(TablePeriods).filter(TablePeriods.Period == period_to_update)\
        .update({r.COL_PERIOD_ISPUBLISHED:status})
    session.commit()
    session.close()

def user_confirm_action_on_period(action,dataset):
    ''' Prompts the user to confirm an action on a dataset (e.g. locking, publishing)

    :param action: Text description of the action (for use in console output)
    :param dataset: Text description of the dataset the action is performed on
    :return: True/False on whether the action should be performed
    '''

    check_status = False
    # Perform additional check only if the user wants to publish a period (i.e. ok to unpublish without checking)
    check_input = raw_input("Please confirm you want to {} {} (Y/N):".format(action, dataset))
    if check_input in ['y', 'Y']:
        check_status = True
    elif check_input in ['n', 'N']:
        pass
    else:
        # Inform the user that the input is incorrect and then abort the publishing process
        util_output("Input '{}' not recognised. Valid inputs are 'Y' or 'N'.".format(check_input))

    return check_status