#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains unit tests for the allocations.py module
'''

import datetime
import unittest

from utils import console_output

class Test_ConsoleOutput(unittest.TestCase):
    ''' Unit tests for the management_accounting.allocations.py module '''


    def test_timestamp_check(self):
        ''' get_all_cost_centres_from_database should return a list of cost centre objects

        :return:
        '''

        test_date_0 = datetime.datetime(year=2017, month=1, day=1)
        test_date_1 = datetime.datetime(year=2017, month=2, day=1)
        test_date_2 = datetime.datetime(year=2017, month=3, day=1)
        test_date_3 = []

        # Check for 2 dates in the correct order
        test_list_of_timestamps = [test_date_0, test_date_1]
        test_result = console_output.first_datetime_not_ascending(list_of_timestamps=test_list_of_timestamps)
        self.assertEqual(test_result, 2)

        # Check for 2 dates in the wrong order
        test_list_of_timestamps = [test_date_1, test_date_0]
        test_result = console_output.first_datetime_not_ascending(list_of_timestamps=test_list_of_timestamps)
        self.assertEqual(test_result, 1)

        # Check for 3 dates in the correct order
        test_list_of_timestamps = [test_date_0, test_date_1, test_date_2]
        test_result = console_output.first_datetime_not_ascending(list_of_timestamps=test_list_of_timestamps)
        self.assertEqual(test_result, 3)

        # Check for 3 dates in the wrong order
        test_list_of_timestamps = [test_date_0, test_date_2, test_date_1]
        test_result = console_output.first_datetime_not_ascending(list_of_timestamps=test_list_of_timestamps)
        self.assertEqual(test_result, 2)

        # Check for 2 dates with one datetime missing
        test_list_of_timestamps = [test_date_0, test_date_3]
        test_result = console_output.first_datetime_not_ascending(list_of_timestamps=test_list_of_timestamps)
        self.assertEqual(test_result, 1)
