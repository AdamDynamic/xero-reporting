#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Purpose of this module is to extract Xero data via the API and import it into the reporting database
'''

import datetime
import pprint

from sqlalchemy.sql import func
from xero import Xero
from xero.auth import PrivateCredentials

from customobjects.database_objects import TableXeroExtract
import references as r
import references_private as rp
from utils.db_connect import db_sessionmaker
import utils.misc_functions


def get_xero_instance():
    ''' Returns an instance of the xero API connection

    :return: xero instance
    '''
    with open(rp.PRIVATE_KEY_LOCATION) as keyfile:
        rsa_key = keyfile.read()

    credentials = PrivateCredentials(consumer_key=rp.CONSUMER_KEY, rsa_key=rsa_key)
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
    assert(year in r.AVAILABLE_PERIODS_YEARS), "year variable must be in the relevant range: {}".format(r.AVAILABLE_PERIODS_YEARS)
    assert(month in r.AVAILABLE_PERIODS_MONTHS), "month variable must be a valid month of the year: {}".format(r.AVAILABLE_PERIODS_MONTHS)

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
    https://stackoverflow.com/questions/11875770/how-to-overcome-datetime-datetime-not-json-serializable-in-python

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
            'trackingCategoryID': rp.CC_XERO_MAPPING_ID,
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

def check_unassigned_costcentres_is_nil(year=None, month=None):
    '''

    :param year:
    :param month:
    :return:
    '''
    # ToDo: Refactor to capture instance where 'unassigned' cost centre across different GLs nets to zero
    # ToDo: Refactor so that only costs are included in allocations (join to allocations table?)
    session = db_sessionmaker()
    date_to_check = datetime.datetime(year=year, month=month, day=1)
    total_unassigned = session.query(func.sum(TableXeroExtract.Value))\
        .filter(TableXeroExtract.CostCentreName==rp.XERO_UNASSIGNED_CC)\
        .filter(TableXeroExtract.Period==date_to_check)\
        .all()
    session.close()

    return (abs(total_unassigned[0][0])<r.ALLOCATIONS_MAX_ERROR) or (total_unassigned[0][0] == None)

def parse_xero_pnl_body_data(xero_data, list_of_cost_centres, year, month):
    ''' Parses the Profit & Loss (split by Cost Centre) report and imports into the database

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

def pull_xero_data_to_database(year, month):
    ''' Pulls data via the Xero API and imports it into the database

    :param year:
    :param month:
    :return:
    '''

    # ToDo: Insert check in instance where no Xero data exists for period

    utils.misc_functions.check_period_exists(year=year, month=month)
    utils.misc_functions.check_period_is_locked(year=year, month=month)
    xero_data = get_xero_profit_and_loss_data(year=year, month=month)
    list_of_costcentres = get_list_of_cost_centres(xero_data=xero_data)

    try:
        session = db_sessionmaker()
        data_rows = parse_xero_pnl_body_data(xero_data=xero_data, list_of_cost_centres=list_of_costcentres, year=year, month=month)

        utils.misc_functions.delete_table_data_for_period(table=TableXeroExtract, year=year, month=month)

        for data_row in data_rows:
            if data_row.Value != 0:
                session.add(data_row)
        session.commit()
    finally:
        session.close()
