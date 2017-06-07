#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Purpose of this module is to extract Xero data
'''

import datetime
import pprint

from sqlalchemy.sql import func
from xero import Xero
from xero.auth import PrivateCredentials

import references as r
import references_private
from customobjects.database_objects import TableXeroExtract, TablePeriods
from utils.db_connect import db_sessionmaker


def get_xero_instance():
    ''' Returns an instance of the xero API connection

    :return: xero instance
    '''
    with open(references_private.PRIVATE_KEY_LOCATION) as keyfile:
        rsa_key = keyfile.read()

    credentials = PrivateCredentials(consumer_key=references_private.CONSUMER_KEY, rsa_key=rsa_key)
    xero = Xero(credentials)

    return xero

def print_tracking_categories():
    ''' Utility function to return all tracking categories currently set up in Xero

    :return:
    '''
    xero = get_xero_instance()
    pprint.pprint(xero.trackingcategories.all())

def get_to_from_date_range(year=None, month=None):
    ''' Calculates the to and from dates for each reporting period, taking into account leap years, months of different lengths, etc

    :param year:
    :param month:
    :return: datetime objects of the first and last day of the month for that year
    '''
    # Check that parameters are in a sensible range
    # ToDo: Refactor this to the references module
    assert(year in [2014,2015,2016,2017,2018,2019,2020]), "year variable must be in the relevant range"
    assert(month in [1,2,3,4,5,6,7,8,9,10,11,12]), "month variable must be a valid month of the year"

    from_date = datetime.datetime(year=year, month=month, day=1)
    to_date = None
    if month==12:
        to_date = datetime.datetime(year=year+1, month=1, day=1)
    else:
        to_date = datetime.datetime(year=year, month=month+1, day=1)
    to_date = to_date + datetime.timedelta(days=-1)

    return from_date, to_date

def json_serial(obj):
    ''' JSON serialiser for objects not serialisable by default JSON code

    (From stackoverflow solution "how to overcome 'datetime.datetime not JSON serializable' in python?)

    :param obj:
    :return:
    '''
    if isinstance(obj, datetime.datetime):
        serial = obj.isoformat()
        return serial
    raise TypeError("Type is not serialisable")

def get_xero_profit_and_loss_data(year=None, month=None):
    ''' Retrieves Profit & Loss data from Xero for a specific period

    :param year:
    :param month:
    :return: A JSON object containing the Profit & Loss account split by cost centre
    '''

    xero = get_xero_instance()

    # Define the to- and from-dates in the YYYY-MM-DD format required by the xero api
    from_date, to_date = get_to_from_date_range(year=year, month=month)
    from_date.strftime('%Y-%m-%d')
    to_date.strftime('%Y-%m-%d')

    # Retrieve the data from xero
    xero_data = xero.reports.get(
        'ProfitAndLoss',
        params={
            'fromDate': from_date,
            'toDate': to_date,
            'trackingCategoryID': r.CC_XERO_MAPPING_ID,
        },
    )
    return xero_data[0]

def get_list_of_cost_centres(xero_data):
    ''' Returns an ordered list of cost centres in the data

    :param xero_data:
    :return:
    '''
    list_of_cost_centres = []
    for row in xero_data['Rows']:
        if row['RowType'] == "Header":
            for cells in row['Cells']:
                for cost_centre in cells.values():
                    list_of_cost_centres.append(cost_centre)
    return list_of_cost_centres

def check_reporting_period_is_locked(year=None, month=None):
    '''

    :param year:
    :param month:
    :return:
    '''

    session = db_sessionmaker()
    period_to_check = datetime.datetime(year=year, month=month,day=1)
    period_query = session.query(TablePeriods).filter(TablePeriods.Period==period_to_check).one()
    session.close
    return period_query.IsLocked

def check_unassigned_costcentres_is_nil(year=None, month=None):
    '''

    :param year:
    :param month:
    :return:
    '''
    # ToDo: Refactor to capture instance where 'unassigned' cost centre across different GLs nets to zero
    session = db_sessionmaker()
    date_to_check = datetime.datetime(year=year, month=month, day=1)
    total_unassigned = session.query(func.sum(TableXeroExtract.Value))\
        .filter(TableXeroExtract.CostCentreName=='Unassigned')\
        .filter(TableXeroExtract.Period==date_to_check)\
        .all()
    session.close()

    return (total_unassigned[0][0] == 0) or (total_unassigned[0][0] == None)

def delete_old_xero_data(year=None, month=None):
    ''' Deletes existing xero data from the tbl_DATA_xeroextract table

    :param year: The year of the period to be deleted
    :param month: The month of the period to be deleted
    :return:
    '''

    session = db_sessionmaker()
    period_to_delete = datetime.datetime(year=year, month=month,day=1)

    period_is_locked = check_reporting_period_is_locked(year=year, month=month)

    if not period_is_locked:
        session.query(TableXeroExtract).filter(TableXeroExtract.Period==period_to_delete).delete()
        session.commit()
        session.close()
    else:
        raise ValueError("Period {}.{} is locked in table {}".format(year, month, r.TBL_MASTER_PERIODS))

def parse_xero_body_data(xero_data, list_of_cost_centres, year, month):
    '''

    :param xero_data:
    :param list_of_cost_centres:
    :return:
    '''

    timestamp = datetime.datetime.now()
    period = datetime.datetime(year=year, month=month,day=1)
    list_of_database_rows = []

    report_name = xero_data['ReportID']
    company_name = xero_data['ReportTitles'][1]

    for row in xero_data['Rows']:
        if row['RowType'] == "Section":
            for section in row['Rows']:
                try:
                    account_name = section['Cells'][0]['Value']
                    account_code = section['Cells'][0]['Attributes'][0]['Value']
                except KeyError, e:
                    pass    # Supress KeyErrors to exclude summary or totals rows (don't have 'Attributes' field)
                else:
                    # Exclude the first cell (the account name) and the last cell (the total)
                    for i in range(1,len(list_of_cost_centres)-1):
                        cost_centre = list_of_cost_centres[i]
                        value = section['Cells'][i]['Value']

                        xero_ledger_entry = TableXeroExtract(
                                                            DateExtracted = timestamp,
                                                            ReportName = report_name,
                                                            CompanyName = company_name,
                                                            CostCentreName = cost_centre,
                                                            AccountCode = account_code,
                                                            AccountName = account_name,
                                                            Period = period,
                                                            Value = value,
                                                            )
                        list_of_database_rows.append(xero_ledger_entry)

    return list_of_database_rows

def pull_xero_data_to_database(year=None, month=None):
    ''' Pulls the xero data via the API and imports it into the management reporting database

    :return:
    '''

    xero_data = get_xero_profit_and_loss_data(year=year, month=month)
    list_of_costcentres = get_list_of_cost_centres(xero_data=xero_data)

    session = db_sessionmaker()

    try:
        data_rows = parse_xero_body_data(xero_data=xero_data, list_of_cost_centres=list_of_costcentres, year=year, month=month)
        for data_row in data_rows:
            if data_row.Value != 0:
                session.add(data_row)

        delete_old_xero_data(year=year, month=month)
        session.commit()
    finally:
        session.close()


    # Performed last to preserve the data in the case of errors in the above process
    # ToDo: Include warning/check to user on execution that this will be done
    #delete_old_xero_data(year=year, month=month)

    # Create database objects for each row and import into the database

    # Once all database objects have been added to the session, add to database


#pull_xero_data_to_database(year=2017, month=3)
#delete_old_xero_data(year=2017, month=5)

#print check_unassigned_costcentres_is_nil(year=2017, month=5)

