#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''

Contains user-defined objects used by the program

'''


class Employee(object):

    def __init__(self):

        self.id = None
        self.first_name = None
        self.last_name = None
        self.job_title = None
        self.start_date = None
        self.end_date = None

        self.salary = None

        self.cost_centre = None
        self.company_code = None

        self.is_perm = None

        # ToDo: Write __repr__ function


class Company(object):

    def __init__(self):

        self.name = None
        self.cost_centres = []


class CostCentre(object):

    def __init__(self):

        self.xero_name = None
        self.xero_code = None
        self.master_name = None
        self.master_code = None
        self.hierarchy_tier = 0

        self.employees = []
        self.direct_costs = []              # List of Cost objects with populated Xero data
        self.allocated_costs = []           # List of Cost objects with allocated cost data Q: how to capture source cost centre?

    def headcount(self):
        return len(self.employees)

    def total_direct_costs(self):
        return sum([c.amount for c in self.direct_costs])

    def total_indirect_costs(self):
        return sum([c.amount for c in self.allocated_costs])

    def __repr__(self):
        return "<CostCentre: Name: {}, Code: {}, Tier: {}>".format(self.master_name, self.master_code, self.hierarchy_tier)


class Cost(object):

    def __init__(self):

        self.amount = 0
        self.ledger_account_code = 0
        self.ledger_account_name = 0
        self.allocation_account_code = 0        # The GL that costs in the account are allocated via
        self.counterparty_costcentre = None
        self.cost_hierarchy = 0
        self.period = None

    def __repr__(self):

        return "<Cost - Account Code: {}, Account Name: {}, Alloc Code: {}, Cost Hierarchy {}, Cpty CC Code: {}, Period: {}, Amount: {}>"\
            .format(self.ledger_account_code,
                    self.ledger_account_name,
                    self.allocation_account_code,
                    self.cost_hierarchy,
                    self.counterparty_costcentre,
                    self.period,
                    self.amount)

