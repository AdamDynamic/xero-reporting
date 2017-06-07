'''

Contains user-defined objects used by the program

'''

from utils.db_connect import db_sessionmaker
from utils.misc_functions import import_csv_to_dict
import references as r

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


def get_all_employee_data():
    ''' Retrieves all employee data from master data

    :return: A list of Employee objects populated with meta-data
    '''

    # 1) Open CSV file and import data
    hr_data = import_csv_to_dict(file_location=r.HR_CSV_FILE_LOCATION)

    # 2) Produce list of Employee objects
    list_of_employees = []
    for employee in hr_data:
        e = Employee()
        e.id = employee[r.EMPLOYEE_ID]
        e.first_name = employee[r.EMPLOYEE_FIRST_NAME]
        e.last_name = employee[r.EMPLOYEE_LAST_NAME]
        e.job_title = employee[r.EMPLOYEE_JOB_TITLE]
        e.start_date = employee[r.EMPLOYEE_START_DATE]
        e.salary = employee[r.EMPLOYEE_SALARY]
        e.is_perm = employee[r.EMPLOYEE_PERM_FLAG]
        e.cost_centre = employee[r.EMPLOYEE_COST_CENTRE]

        list_of_employees.append(e)

    return list_of_employees

# def get_all_cost_centres():
#
#     # 1) Open CSV file and import data
#     cc_data = import_csv_to_dict(file_location=r.CC_CSV_FILE_LOCATION)
#
#     # 2) Produce list of Cost Centre objects
#     list_of_costcentres = []
#
#     for cc in cc_data:
#         c = CostCentre()
#         c.xero_name = cc[r.CC_XERO_NAME]
#         c.xero_code = cc[r.CC_XERO_MAPPING]
#         c.master_name = cc[r.CC_CLEARMATICS_MAPPING]
#         c.is_support_function = cc[r.CC_IS_SUPPORT_FUNCTION]
#         list_of_costcentres.append(c)



