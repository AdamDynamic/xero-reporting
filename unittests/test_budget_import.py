#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains unit tests for the budget_import .py module
'''

import unittest

import budget.budget_import as budget_import
import datetime

class Test_BudgetImport(unittest.TestCase):
    ''' Unit tests for the management_accounting.allocations.py module '''


    def test_datetime_conversion_with_slashes(self):
        ''' Checks that the conversion of dates from strings adheres to the UK formatting standard

        :return:
        '''

        test_input_1 = '01/09/2018'
        expected_result_1 = datetime.datetime(2018,9,1,0,0)

        test_result_1 = budget_import.convert_string_to_datetime(input_date=test_input_1)
        self.assertEqual(test_result_1, expected_result_1)

        test_input_2 = '01/01/2018'
        expected_result_2 = datetime.datetime(2018,1,1,0,0)

        test_result_2 = budget_import.convert_string_to_datetime(input_date=test_input_2)
        self.assertEqual(test_result_2, expected_result_2)

    def test_datetime_conversion_with_dashes(self):
        ''' Checks that the conversion of dates from strings adheres to the UK formatting standard

        :return:
        '''

        test_input_1 = '2018-09-01'
        expected_result_1 = datetime.datetime(2018,9,1,0,0)

        test_result_1 = budget_import.convert_string_to_datetime(input_date=test_input_1)
        self.assertEqual(test_result_1, expected_result_1)

        test_input_2 = '2018-01-01'
        expected_result_2 = datetime.datetime(2018,1,1,0,0)

        test_result_2 = budget_import.convert_string_to_datetime(input_date=test_input_2)
        self.assertEqual(test_result_2, expected_result_2)

    def test_datetime_conversion_with_spaces(self):
        ''' Checks that the conversion of dates from strings adheres to the UK formatting standard

        :return:
        '''

        test_input_1 = '2018-12-01 07:47:28'
        expected_result_1 = datetime.datetime(2018,12,1,7,47,28)

        test_result_1 = budget_import.convert_string_to_datetime(input_date=test_input_1)
        self.assertEqual(test_result_1, expected_result_1)
