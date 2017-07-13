#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains unit tests for the misc_functions.py module
'''

import datetime
import unittest

import utils.data_integrity
from customobjects import error_objects
from utils import misc_functions
import references as r

class Test_MiscFunctions(unittest.TestCase):

    def test_get_datetime_of_last_day_of_month(self):
        ''' get_datetime_of_last_day_of_month should return a datetime object one day earlier than the first day of the previous month

        :return:
        '''

        test_year=2016
        test_month=2

        test_result = misc_functions.get_datetime_of_last_day_of_month(year=test_year, month=test_month)
        expected_result = datetime.datetime(year=2016, month=2, day=29)
        self.assertEqual(test_result, expected_result)

    def test_check_period_exists(self):
        ''' check_period_exists should raise error if an invalid input is passed to the function

        :return:
        '''

        error_years=[2000, 'abc', -2000]
        error_months = [None, -1, 13, 100, 'abc']
        correct_year = r.AVAILABLE_PERIODS_YEARS[0]
        correct_month = r.AVAILABLE_PERIODS_MONTHS[-1]

        for error_year in error_years:
            for error_month in error_months:
                self.assertRaises(error_objects.PeriodNotFoundError, utils.data_integrity.check_period_exists, error_year, correct_month)
                self.assertRaises(error_objects.PeriodNotFoundError, utils.data_integrity.check_period_exists, error_year, error_month)
                self.assertRaises(error_objects.PeriodNotFoundError, utils.data_integrity.check_period_exists, correct_year, error_month)
