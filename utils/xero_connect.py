#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Purpose of this module is to extract Xero data via the API and import it into the reporting database
'''

import datetime
import pprint

from xero import Xero
from xero.auth import PrivateCredentials

import utils.data_integrity
from customobjects.database_objects import TableXeroExtract, TableAllocationAccounts, TableChartOfAccounts
import customobjects.error_objects
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

def get_to_from_date_range(year, month):
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

def get_xero_profit_and_loss_data(year, month):
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


def get_xero_balancesheet_data(year, month):
    ''' Retrieves Balance Sheet data from Xero for a specific period

    :param year:
    :param month:
    :return: A JSON object containing the Balance Sheet
    '''

    xero = get_xero_instance()

    # Define the to- and from-dates in the YYYY-MM-DD format required by the xero api
    from_date, to_date = get_to_from_date_range(year=year, month=month)
    from_date.strftime('%Y-%m-%d')
    to_date.strftime('%Y-%m-%d')

    # Retrieve the data from xero
    xero_data = xero.reports.get(
        'BalanceSheet',
        params={
            'date': to_date,    # Only use to_date in order to capture the balance on the last day of the period
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

def check_unassigned_costcentres_is_nil(year, month):
    ''' Checks that any L1 nodes that must reallocate its costs has no costs that have no cost centre allocated

    :param year:
    :param month:
    :return:
    '''

    session = db_sessionmaker()
    date_to_check = datetime.datetime(year=year, month=month, day=1)
    total_unassigned = session.query(TableXeroExtract, TableChartOfAccounts, TableAllocationAccounts)\
        .filter(TableXeroExtract.AccountCode==TableChartOfAccounts.XeroCode)\
        .filter(TableChartOfAccounts.L3Code == TableAllocationAccounts.L2Hierarchy) \
        .filter(TableXeroExtract.CostCentreName == rp.XERO_UNASSIGNED_CC) \
        .filter(TableXeroExtract.Period==date_to_check)\
        .all()
    session.close()

    L1_nodes = list(set([coa.L1Code for xero, coa, alloc_ac in total_unassigned]))

    # Each L1 node should net to zero so that no unassigned costs are allocated to receiver cost centres
    for L1_node in L1_nodes:
        total_unallocated = abs(sum([xero.Value for xero, coa, alloc_ac in total_unassigned if coa.L1Code==L1_node]))
        if total_unallocated > r.DEFAULT_MAX_CALC_ERROR:
            raise customobjects.error_objects.UnallocatedCostsNotNilError(
                "Costs in cost centre '{}' for L1 node {} are not net flat (total = {})"
                    .format(rp.XERO_UNASSIGNED_CC, L1_node, total_unallocated))

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

def parse_xero_balancesheet_body_data(xero_data, year, month):
    ''' Parses the Balance Sheet report and creates a list of database rows

    :param xero_data: Raw Xero output from the API
    :param year:
    :param month:
    :return: List of TableXeroExtract row objects populated with data
    '''

    # ToDo: Refactor to combine parsing of Balance Sheet and Income Statement functions

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
                    # Exclude the first cell (the account name) and the last cell (prior year comparator)
                    value = section['Cells'][1]['Value']
                    xero_ledger_entry = TableXeroExtract(
                                                        DateExtracted=timestamp,
                                                        ReportName=report_name,
                                                        CompanyName=company_name,
                                                        CostCentreName=None,
                                                        AccountCode=account_code,
                                                        AccountName=account_name,
                                                        Period=period,
                                                        Value=value,
                                                    )

                    list_of_database_rows.append(xero_ledger_entry)

    return list_of_database_rows

def pull_xero_data_to_database(year, month):
    ''' Pulls data via the Xero API and imports it into the database

    :param year:
    :param month:
    :return:
    '''

    # Check that the period exists and is valid
    utils.data_integrity.master_data_integrity_check(year=year, month=month, check_balance_sheet=False)

    # Pull both the Income Statement data and Balance Sheet data from the API
    pnl_xero_data = get_xero_profit_and_loss_data(year=year, month=month)
    list_of_costcentres = get_list_of_cost_centres(xero_data=pnl_xero_data) # Used for the Income Statement only
    bs_xero_data = get_xero_balancesheet_data(year=year, month=month)

    try:
        session = db_sessionmaker()
        pnl_data_rows = parse_xero_pnl_body_data(xero_data=pnl_xero_data, list_of_cost_centres=list_of_costcentres,
                                                 year=year, month=month)

        bs_data_rows = parse_xero_balancesheet_body_data(xero_data=bs_xero_data, year=year, month=month)

        # Data should exist for all periods in Xero
        if not pnl_data_rows or not bs_data_rows:
            raise customobjects.error_objects.TableEmptyForPeriodError("No data exists in Xero for period {}.{}"
                                                                       " ({} records returned for Income Statement,"
                                                                       " {} records returned for Balance Sheet)"
                                                                       .format(year, month, len(pnl_data_rows), len(bs_data_rows)))

        utils.misc_functions.delete_table_data_for_period(table=TableXeroExtract, year=year, month=month)

        for data_row in pnl_data_rows:
            if data_row.Value != 0:
                session.add(data_row)

        for data_row in bs_data_rows:
            if data_row.Value != 0:
                session.add(data_row)

        session.commit()

    finally:
        session.close()
