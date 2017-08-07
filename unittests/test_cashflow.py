#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains unit tests for the allocations.py module
'''

import datetime
import unittest

from management_accounting import cashflow_calcs
from customobjects.database_objects import TableConsolidatedFinStatements

CURRENT_YEAR = 2017
PREVIOUS_YEAR = 2016

CURRENT_MONTH = 1
PREVIOUS_MONTH = 12

CURRENT_VALUE = 1000
PREVIOUS_VALUE = 2000

COMPANY_CODE = 1000

BS_L2_TEST_NODE = 'bs_L2_test_node'

def get_test_data_rows():
    ''' Returns pre-populated data rows as input into the functions by create_internal_cashflow_statement

    :return:
    '''

    current_period = datetime.datetime(year=CURRENT_YEAR, month=CURRENT_MONTH, day=1)
    previous_period = datetime.datetime(year=PREVIOUS_YEAR, month=PREVIOUS_MONTH, day=1)

    current_row = TableConsolidatedFinStatements(
        ID=None,
        Period=current_period,
        CompanyCode=COMPANY_CODE,
        CompanyName=None,
        PartnerCompanyCode=None,
        PartnerCompanyName=None,
        CostCentreCode=None,
        CostCentreName=None,
        PartnerCostCentreCode=None,
        PartnerCostCentreName=None,
        FinancialStatement=None,
        GLAccountCode=None,
        GLAccountName=None,
        L1Code=None,
        L1Name=None,
        L2Code=BS_L2_TEST_NODE,
        L2Name=None,
        L3Code=None,
        L3Name=None,
        CostHierarchyNumber=None,
        Value=CURRENT_VALUE,
        TimeStamp=None
    )

    previous_row = TableConsolidatedFinStatements(
        ID=None,
        Period=previous_period,
        CompanyCode=COMPANY_CODE,
        CompanyName=None,
        PartnerCompanyCode=None,
        PartnerCompanyName=None,
        CostCentreCode=None,
        CostCentreName=None,
        PartnerCostCentreCode=None,
        PartnerCostCentreName=None,
        FinancialStatement=None,
        GLAccountCode=None,
        GLAccountName=None,
        L1Code=None,
        L1Name=None,
        L2Code=BS_L2_TEST_NODE,
        L2Name=None,
        L3Code=None,
        L3Name=None,
        CostHierarchyNumber=None,
        Value=PREVIOUS_VALUE,
        TimeStamp=None
    )

    return[current_row, previous_row]


class Test_CashFlow(unittest.TestCase):

    def test_change_in_balancesheet_value(self):
        ''' Tests whether the indirect method for calculating cashflow from investments works'''

        test_rows = get_test_data_rows()

        test_result = cashflow_calcs.calculate_change_in_balancesheet_value(CURRENT_YEAR,
                                                                            CURRENT_MONTH,
                                                                            COMPANY_CODE,
                                                                            BS_L2_TEST_NODE,
                                                                            test_rows)

        expected_result = CURRENT_VALUE-PREVIOUS_VALUE
        self.assertEqual(test_result, expected_result)
