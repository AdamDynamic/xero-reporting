#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains unit tests for the allocations.py module
'''

import unittest

from customobjects.helper_objects import Cost, CostCentre, Employee
from management_accounting import allocations

TEST_PERIOD_YEAR = 2017
TEST_PERIOD_MONTH = 5

class Test_EventMatching(unittest.TestCase):
    ''' Unit tests for the DataImport.EventMatching.py module '''


    def test_get_all_cost_centres_from_database_returns_cost_centre_objects(self):
        ''' get_all_cost_centres_from_database should return a list of cost centre objects

        :return:
        '''

        test_result = allocations.get_all_cost_centres_from_database()
        for object in test_result:
            self.assertIsInstance(object, CostCentre)

    def test_get_all_employees_from_database_returns_employee_objects(self):
        ''' get_all_employees_from_database should return a list of employee objects

        :return:
        '''

        test_result = allocations.get_all_employees_from_database(year=TEST_PERIOD_YEAR, month=TEST_PERIOD_MONTH)
        for object in test_result:
            self.assertIsInstance(object, Employee)

    def test_get_direct_costs_by_cc_by_node_returns_dict(self):
        ''' get_direct_costs_by_cc_by_node returns dictionary where each item is a list of Cost objects

        :return:
        '''

        test_result = allocations.get_direct_costs_by_cc_by_node(year=TEST_PERIOD_YEAR, month=TEST_PERIOD_MONTH)
        self.assertIsInstance(test_result, dict)

        # Test that each key in the dictionary relates to a list of cost objects
        for key in test_result.keys():
            for object in test_result[key]:
                self.assertIsInstance(object, Cost)

    def test_get_populated_costcentres_returns_costcentres(self):
        ''' get_populated_costcentres returns a list of cost centre objects

        :return:
        '''

        test_result = allocations.get_populated_costcentres(year=TEST_PERIOD_YEAR, month=TEST_PERIOD_MONTH)

        # Confirm that each object returned is a CostCentre object
        for object in test_result:
            self.assertIsInstance(object, CostCentre)

    def test_get_populated_costcentres_returns_complete_list(self):
        ''' get_populated_costcentres should return cost centres that capture all costs

        :return:
        '''

        test_costcentres = allocations.get_populated_costcentres(year=TEST_PERIOD_YEAR, month=TEST_PERIOD_MONTH)

        total_costcentre_costs = 0
        for cc in test_costcentres:
            total_costcentre_costs += sum([cost.amount for cost in cc.direct_costs])

        total_nodes = allocations.get_direct_costs_by_cc_by_node(year=TEST_PERIOD_YEAR, month=TEST_PERIOD_MONTH)

        total_node_costs = 0
        for cc in total_nodes.keys():
            total_node_costs += sum([cost.amount for cost in total_nodes[cc]])

        self.assertEqual(total_node_costs, total_costcentre_costs)

    def test_get_allocation_percentages_for_hierarchy_level_sums_to_one(self):
        '''

        :return:
        '''

        populated_costcentres = allocations.get_populated_costcentres(year=TEST_PERIOD_YEAR, month=TEST_PERIOD_MONTH)

        hierarchy_levels = [cc.hierarchy_tier for cc in populated_costcentres]

        for level in hierarchy_levels:
            if level != 1:
                test_allocation_percentages = allocations.get_allocation_percentages_for_hierarchy_level(costcentres=populated_costcentres,
                                                                                                 hierarchy_level_to_allocate=level)
                print test_allocation_percentages
                # Check that the allocation percentages sum to one
                for cc_code in test_allocation_percentages.keys():
                    total_percentage = sum([perc for perc in test_allocation_percentages[cc_code].values()])
                    self.assertEqual(total_percentage, 1)

                # Check that the cost centre doesn't allocate to itself
                for cc in populated_costcentres:
                    if cc.master_code in test_allocation_percentages.keys():
                        self.assertNotIn(cc.master_code, test_allocation_percentages[cc.master_code].keys())

                # Test that the cost centre doesn't allocate to levels lower than itself
                for cc_code in test_allocation_percentages.keys():

                    # Identify the code of the key cost centre
                    sender_hierarchy_level = 0
                    for cc in populated_costcentres:
                        if cc.master_code == cc_code:
                            sender_hierarchy_level = cc.hierarchy_tier

                    # Iterate through the cost centre allocated to and assert the level is higher than the sender
                    for alloc_cc_code in test_allocation_percentages[cc_code].keys():
                        for cc in populated_costcentres:
                            if cc.master_code==alloc_cc_code:
                                self.assertLess(cc.hierarchy_tier,sender_hierarchy_level)





        # Test sums to one
        # Test cc doesn't allocate to itself
        # Test that cc doesn't allocate to hierarchy on lower levels

    def test_allocate_dir_costs_for_tier(self):

        alloc_perc = {'C000002': {'C000001': 1.0}, 'C000003': {'C000001': 1.0}}

        level = 2
        sender_cc_directcosts_1 = 2000
        sender_cc_directcosts_2 = 3000

        receiver_cc = CostCentre()
        receiver_cc.master_code = 'C000001'

        # Create sender cost centres to allocate the costs to the receiver
        sender_cc_1 = CostCentre()
        sender_cc_1.master_code = 'C000002'
        cost1 = Cost()
        cost1.amount = sender_cc_directcosts_1 * 1.0
        sender_cc_1.direct_costs.append(cost1)

        sender_cc_2 = CostCentre()
        sender_cc_2.master_code = 'C000003'
        cost2 = Cost()
        cost2.amount = sender_cc_directcosts_2 * 1.0
        sender_cc_2.direct_costs.append(cost2)

        receiver_costcentres = [receiver_cc]
        sender_costcentres = [sender_cc_1, sender_cc_2]

        test_sender_result, test_receiver_result = allocations.allocate_dir_costs_for_tier(sender_costcentres=sender_costcentres,
                                                                                           receiving_costcentres=receiver_costcentres, alloc_percentages=alloc_perc, level=level)

        # Confirm that the costs allocated from the sender cost centres equals the total allocated cost
        total_sender_direct_costs = 0
        for cc in test_sender_result:
            total_sender_direct_costs += sum([cost.amount for cost in cc.direct_costs])


        total_sender_indirect_costs = 0
        for cc in test_sender_result:
            total_sender_indirect_costs += sum([cost.amount for cost in cc.allocated_costs])

        self.assertEqual(total_sender_direct_costs, sender_cc_directcosts_1 + sender_cc_directcosts_2)
        self.assertEqual(total_sender_indirect_costs, (sender_cc_directcosts_1 + sender_cc_directcosts_2) * -1.0)

        # Confirm that the received costs equals the allocated cost
        total_received_costs = 0
        for cc in test_receiver_result:
            total_received_costs += sum([cost.amount for cost in cc.allocated_costs])

        self.assertEqual(total_received_costs, sender_cc_directcosts_1 + sender_cc_directcosts_2)


        # ToDo: Check that cpty_costcentres aren't allocating costs to themselves

