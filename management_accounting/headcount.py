#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Creates the headcount rows for the consolidated table
'''

import datetime

from dateutil.relativedelta import relativedelta
import references as r
from sqlalchemy import or_

from customobjects.database_objects import TableConsolidatedFinStatements, TableHeadcount,\
    TableCompanies, TableCostCentres
from utils.db_connect import db_sessionmaker


def get_headcount_rows(year, month, time_stamp=None):
    ''' Creates rows for the Consolidated Financial Statement table that reflects headcount for the period

    :param year: Year for the period to get headcount for
    :param month: Month for the period to get headcout for
    :return: TableConsolidatedFinStatements row objects
    '''

    # Only need headcount for employees in the business during the month
    start_date = datetime.datetime(year=year, month=month, day=1)
    end_date = datetime.datetime(year=year, month=month, day=1) + relativedelta(months=1) + relativedelta(days=-1)

    # Get all headcount at the end of the period that have started but haven't left
    session = db_sessionmaker()
    headcount_qry = session.query(TableHeadcount, TableCompanies, TableCostCentres)\
        .filter(TableHeadcount.StartDate<=start_date)\
        .filter(or_(TableHeadcount.EndDate>end_date,TableHeadcount.EndDate==None))\
        .filter(TableHeadcount.CompanyCode==TableCompanies.CompanyCode)\
        .filter(TableHeadcount.CostCentreCode==TableCostCentres.CostCentreCode)\
        .all()
    session.close()

    # Want the headcount grouped by cost centre, company code,
    populated_rows = []

    for headcount, comp, cc in headcount_qry:

        row = TableConsolidatedFinStatements(
            Period=start_date,
            CompanyCode=comp.CompanyCode,
            CompanyName=comp.CompanyName,
            PartnerCompanyCode=None,
            PartnerCompanyName=None,
            CostCentreCode=cc.CostCentreCode,
            CostCentreName=cc.CostCentreName,
            PartnerCostCentreCode=None,
            PartnerCostCentreName=None,
            FinancialStatement=r.CM_DATA_HEADCOUNT,
            GLAccountCode=r.CM_HC_GL,
            GLAccountName=headcount.FirstName + " " + headcount.LastName + " (" + headcount.JobTitle + ")",
            L1Code=r.CM_HC_L1,
            L1Name=r.CM_HC_L1,
            L2Code=r.CM_HC_L2,
            L2Name=r.CM_HC_L2,
            L3Code=r.HEADCOUNT_CODE_CONTRACTOR if headcount.IsContractor else r.HEADCOUNT_CODE_PERMANENT,
            L3Name=r.HEADCOUNT_CODE_CONTRACTOR if headcount.IsContractor else r.HEADCOUNT_CODE_PERMANENT,
            CostHierarchyNumber=None,
            Value=headcount.FTE,
            TimeStamp = time_stamp if time_stamp else start_date
        )

        populated_rows.append(row)

    return populated_rows
