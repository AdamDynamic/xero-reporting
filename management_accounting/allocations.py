#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains the functions used to generate indirect cost allocations

Configuration assumes that indirect cost allocations are performed using relative FTE (not headcount) in each cost centre.
'''

import datetime

from sqlalchemy import or_

from customobjects.database_objects import \
    TableCostCentres, \
    TableFinancialStatements, \
    TableChartOfAccounts, \
    TableAllocationAccounts, \
    TableAllocationsData, \
    TableHeadcount,\
    TableNodeHierarchy, \
    TableFinModelExtract, \
    TableBudgetAllocationsData
from customobjects.helper_objects import CostCentre, Employee, Cost
import references as r
from utils.db_connect import db_sessionmaker
import utils.data_integrity
import utils.misc_functions


def get_all_cost_centres_from_database():
    ''' Returns a list of CostCentre objects populated with master data information

    :param year:
    :param month:
    :return:
    '''

    session = db_sessionmaker()
    qry_costcentres = session.query(TableCostCentres).all()
    session.close()

    list_of_costcentres = []
    for row in qry_costcentres:
        cc = CostCentre()
        cc.master_name = row.CostCentreName
        cc.master_code = row.CostCentreCode
        cc.hierarchy_tier = row.AllocationTier
        cc.employees = []

        list_of_costcentres.append(cc)

    return list_of_costcentres

### Actuals Data

def get_all_actuals_employees_from_database(year, month):
    ''' Returns a list of Employee objects based on the Actuals headcount for a given period

    :param year:
    :param month:
    :return:
    '''

    session = db_sessionmaker()

    # Period takes the headcount as of the last day of the month
    period = utils.misc_functions.get_datetime_of_last_day_of_month(year=year, month=month)

    qry_headcount = session.query(TableHeadcount)\
        .filter(TableHeadcount.StartDate <= period)\
        .filter(or_(TableHeadcount.EndDate >= period, TableHeadcount.EndDate == None))\
        .all()

    session.close()

    list_of_employees = []

    for row in qry_headcount:
        emp = Employee()
        emp.id = row.EmployeeID
        emp.first_name = row.FirstName
        emp.last_name = row.LastName
        emp.job_title = row.JobTitle
        emp.start_date = row.StartDate
        emp.end_date = row.EndDate
        emp.cost_centre = row.CostCentreCode
        emp.company_code = row.CompanyCode
        emp.fte = row.FTE

        list_of_employees.append(emp)

    return list_of_employees

def get_direct_costs_actuals_by_cc_by_node(year, month):
    ''' Get the direct costs (actuals) split by cost centre and L2 hierarchy level for a given period

    :param year:
    :param month:
    :return:
    '''

    session = db_sessionmaker()
    period = datetime.datetime(year=year, month=month, day=1)
    qry_costs = session.query(TableFinancialStatements, TableChartOfAccounts, TableNodeHierarchy, TableAllocationAccounts)\
        .filter(TableFinancialStatements.AccountCode == TableChartOfAccounts.GLCode)\
        .filter(TableChartOfAccounts.L3Code == TableNodeHierarchy.L3Code)\
        .filter(TableNodeHierarchy.L2Code == TableAllocationAccounts.L2Hierarchy)\
        .filter(TableFinancialStatements.Period == period)\
        .all()
    session.close()

    assert qry_costs != [], "Query in get_direct_costs_actuals_by_cc_by_node returned no results for period {}.{}".format(year, month)
    output_dict = {}
    # Get all cost centres in the extracted data
    list_of_costcentres = list(set([pnl.CostCentreCode for pnl, coa, node, alloc in qry_costs]))
    # Get all cost categories in the extracted data
    list_of_costcategories = list(set([(node.L2Code, alloc.GLCode) for pnl, coa, node, alloc in qry_costs]))

    # Create cost objects for each cost centre for each hierarchy node
    output_dict = {}
    for cc in list_of_costcentres: # e.g. C000001, C000002, etc
        list_of_costs = []
        for costcategory in list_of_costcategories: # e.g. L2-FIN, L2-STAFF, etc
            cost = Cost()
            cost.period = period
            cost.master_code = costcategory[0]
            cost.allocation_account_code = costcategory[1]
            cost.amount = sum([pnl.Value for pnl, coa, node, alloc in qry_costs if pnl.CostCentreCode == cc and node.L2Code == costcategory[0]])
            if abs(cost.amount) > r.DEFAULT_MAX_CALC_ERROR:    # Filter out near-zero costs to reduce number of records up-stream
                list_of_costs.append(cost)
        output_dict[cc]=list_of_costs

    return output_dict

def get_populated_costcentres_actuals(year=None, month=None):
    ''' Returns a list of cost centres populated with actuals direct costs and employees in each cost centre

    :param year:
    :param month:
    :return:
    '''

    list_of_costcentres = get_all_cost_centres_from_database()
    list_of_employees = get_all_actuals_employees_from_database(year=year, month=month)
    direct_costs_for_period = get_direct_costs_actuals_by_cc_by_node(year=year, month=month)

    for cc in list_of_costcentres:
        cc.employees = [emp for emp in list_of_employees if emp.cost_centre==cc.master_code]
        try:
            cc.direct_costs = direct_costs_for_period[cc.master_code]
        except KeyError:
            pass # If the cost centre has no costs for that period

    return list_of_costcentres

### Budget Data

def get_all_budget_periods(label):
    ''' Returns a list of (year, month) tuples representing all periods available in the budget data for a given label

    :param label: Tag used for specfic set of Budget data
    :return:
    '''

    session = db_sessionmaker()
    all_dates = session.query(TableFinModelExtract.Period).filter(TableFinModelExtract.Label == label).all()
    session.close()

    # Remove all duplicates from the list of periods
    output = list(set([(d[0].year, d[0].month) for d in all_dates]))
    output.sort()

    return output

def get_all_budget_employees_from_database(year, month, label):
    ''' Returns a list of Employee objects for a given period and a given Budget dataset

    :param year:
    :param month:
    :param label:
    :return:
    '''

    period_to_retrieve = datetime.datetime(year=year, month=month, day=1)

    # Get the data from the database
    session = db_sessionmaker()
    # ToDo: Refactor to capture GLs for perm and contract
    qry_headcount = session.query(TableFinModelExtract)\
        .filter(TableFinModelExtract.Label == label)\
        .filter(TableFinModelExtract.Period == period_to_retrieve)\
        .filter(or_(TableFinModelExtract.GLCode == r.CM_HC_GL_CONTRACT,TableFinModelExtract.GLCode == r.CM_HC_GL_PERMANENT))\
        .all()
    session.close()

    list_of_employees = []

    # Create a list of Employee objects that will be used for allocations
    for row in qry_headcount:
        emp = Employee()
        emp.id = None
        emp.first_name = None
        emp.last_name = None
        emp.fte = row.Value
        emp.job_title = None
        emp.start_date = None
        emp.end_date = None
        emp.cost_centre = row.CostCentreCode
        emp.company_code = row.CompanyCode

        list_of_employees.append(emp)

    return list_of_employees

def get_direct_costs_budget_by_cc_by_node(year, month, label):
    '''

    :param year:
    :param month:
    :param label:
    :return:
    '''
    period = datetime.datetime(year=year, month=month, day=1)

    session = db_sessionmaker()
    qry_costs = session.query(TableFinModelExtract, TableChartOfAccounts, TableNodeHierarchy, TableAllocationAccounts)\
        .filter(TableFinModelExtract.GLCode == TableChartOfAccounts.GLCode)\
        .filter(TableChartOfAccounts.L3Code == TableNodeHierarchy.L3Code)\
        .filter(TableNodeHierarchy.L2Code == TableAllocationAccounts.L2Hierarchy)\
        .filter(TableFinModelExtract.Period == period)\
        .filter(TableFinModelExtract.Label == label)\
        .all()
    session.close()

    assert qry_costs != [], "Query in get_direct_costs_budget_by_cc_by_node for {} returned no results for period {}.{}"\
        .format(label,year, month)

    list_of_costcentres = list(set([fin.CostCentreCode for fin, coa, node, alloc in qry_costs]))
    list_of_costcategories = list(set([(node.L2Code, alloc.GLCode) for fin, coa, node, alloc in qry_costs]))

    # Create cost objects for each cost centre for each hierarchy node
    output_dict = {}
    for cc in list_of_costcentres: # e.g. C000001, C000002, etc
        list_of_costs = []
        for costcategory in list_of_costcategories: # e.g. L2-FIN, L2-STAFF, etc
            cost = Cost()
            cost.period = period
            cost.master_code = costcategory[0]
            cost.allocation_account_code = costcategory[1]
            cost.amount = sum([pnl.Value for pnl, coa, node, alloc in qry_costs if pnl.CostCentreCode == cc and node.L2Code == costcategory[0]])
            if abs(cost.amount) > r.DEFAULT_MAX_CALC_ERROR:    # Filter out near-zero costs to reduce number of records up-stream
                list_of_costs.append(cost)
        output_dict[cc]=list_of_costs

    return output_dict

def get_populated_costcentres_budget(year, month, label):
    ''' Returns a list of cost centres populated with budget direct costs and employees in each cost centre

    :param year:
    :param month:
    :param label:
    :return:
    '''

    list_of_costcentres = get_all_cost_centres_from_database()
    list_of_employees = get_all_budget_employees_from_database(year=year, month=month, label=label)
    direct_costs_for_period = get_direct_costs_budget_by_cc_by_node(year=year, month=month, label=label)

    for cc in list_of_costcentres:
        cc.employees = [emp for emp in list_of_employees if emp.cost_centre==cc.master_code]
        try:
            cc.direct_costs = direct_costs_for_period[cc.master_code]
        except KeyError:
            pass # If the cost centre has no costs for that period

    return list_of_costcentres

### Allocate Costs (both Budget and Actuals)

def get_allocation_percentages_for_hierarchy_level(costcentres, hierarchy_level_to_allocate):
    ''' Calculates the percentages each cost centre must allocate to every other cost centre based on FTE of each cc

    :param hierarchy_level_to_allocate:
    :return: Nested dictionary in the form {cc1 : {cc2: 0.5, cc3: 0.4, cc4: 0.1}, cc2 : {...}
    '''
    output_dict = {}

    sender_costcentres = [cc for cc in costcentres if cc.hierarchy_tier == hierarchy_level_to_allocate]
    receiving_costcentres = [cc for cc in costcentres if cc.hierarchy_tier < hierarchy_level_to_allocate]

    total_receiving_fte = 0

    for cc in receiving_costcentres:
        total_receiving_fte += cc.fte()

    assert total_receiving_fte !=0

    for sender_cc in sender_costcentres:
        receiving_dict = {}
        for reciving_cc in receiving_costcentres:
            receiving_dict[reciving_cc.master_code] = reciving_cc.fte()/total_receiving_fte

        # Sense check that the sending cost centre is allocating 100% of its costs
        total_alloc_percs = sum([receiving_dict[cc] for cc in receiving_dict.keys()])
        assert abs((total_alloc_percs - 1.0))<0.00000001,\
            "Sum of allocation percentages {} is != 1.0:\n{}".format(total_alloc_percs, receiving_dict)

        output_dict[sender_cc.master_code] = receiving_dict

    return output_dict

def allocate_dir_costs_for_tier(sender_costcentres, receiving_costcentres, alloc_percentages, level):
    ''' For a given allocation tier, allocate the indirect costs

    :param sender_costcentres: A list of CostCentre objects who are having their costs allocated from them
    :param receiving_costcentres: A list of CostCentre objects who are having costs allocated to them from the sender_costcentres
    :param alloc_percentages: Nested dictionary in the form {cc1 : {cc2: 0.5, cc3: 0.4, cc4: 0.1}, cc2 : {...}
    :param level:
    :return:
    '''

    for receiving_cc in receiving_costcentres:
        for sender_cc in sender_costcentres:

            # Allocate the direct costs in the sender cost centre to the receiving cost centre
            direct_costs_to_allocate = [cost for cost in sender_cc.direct_costs]
            for cost in direct_costs_to_allocate:
                if cost.amount != 0:

                    allocated_cost = alloc_percentages[sender_cc.master_code][receiving_cc.master_code] * float(cost.amount)

                    if allocated_cost != 0:
                        received_cost = Cost()
                        received_cost.amount = allocated_cost
                        received_cost.counterparty_costcentre = sender_cc.master_code
                        received_cost.period = cost.period
                        received_cost.ledger_account_code = cost.allocation_account_code
                        received_cost.cost_hierarchy = level - 1   # Increment the level so that it matches the level it will be reported against

                        receiving_cc.allocated_costs.append(received_cost)

                        # Reverse the polarity and append to the sending cost centre
                        sent_cost = Cost()
                        sent_cost.amount = allocated_cost * -1.0
                        sent_cost.counterparty_costcentre = receiving_cc.master_code
                        sent_cost.period = cost.period
                        sent_cost.ledger_account_code = cost.allocation_account_code
                        sent_cost.cost_hierarchy = level - 1

                        sender_cc.allocated_costs.append(sent_cost)

                        assert received_cost.cost_hierarchy >= 1, "Cost hierarchy level is {}".format(received_cost.cost_hierarchy)

        # Check that the costs are completely allocated and that direct costs equals indirect costs
        # This is to ensure that the whole process is net-flat at a company level
    for cc in sender_costcentres:
        total_direct_costs = sum([cost.amount for cost in cc.direct_costs])
        total_allocated_costs = sum([cost.amount for cost in cc.allocated_costs if cost.cost_hierarchy==level-1])
        assert abs(float(total_direct_costs)+float(total_allocated_costs))<r.DEFAULT_MAX_CALC_ERROR, "Total direct costs {} not equal allocated costs {} for cc \n{}\n{}\n{}"\
            .format(total_direct_costs, total_allocated_costs, cc, [cost for cost in cc.direct_costs], [cost for cost in cc.allocated_costs])

    return (sender_costcentres, receiving_costcentres)

def reallocate_previously_allocated_costs(sender_costcentres=None, receiving_costcentres=None, alloc_percentages=None, level=None):
    ''' Previously allocated costs must be allocated to the next level

    :param sender_costcentres: The cost centre sending (i.e. allocating) the costs
    :param receiving_costcentres: The cost centre receiving the allocated costs
    :param alloc_percentages: The allocation percentages detailing what percentage of costs should be allocated to each
            receiving cost centre by the sender cost centre
    :param level: The hierarchy level of the allocations
    :return:
    '''

    for receiving_cc in receiving_costcentres:
        for sender_cc in sender_costcentres:

            assert sender_cc.master_code != receiving_cc.master_code # A cost centre can't allocate costs to itself

            # Only re-allocate costs from the previous allocation cycle
            indirect_costs_to_allocate = [cost for cost in sender_cc.allocated_costs if cost.cost_hierarchy==level]

            for previously_allocated_cost in indirect_costs_to_allocate:

                # Append a reversing duplicate cost to the sender_cc so that when viewed at the new hierarchy level,
                # the cost nets to nil at the previous level
                reallocated_cost = previously_allocated_cost.amount * alloc_percentages[sender_cc.master_code][receiving_cc.master_code]
                if reallocated_cost != 0:

                    received_cost = Cost()
                    received_cost.cost_hierarchy = level - 1
                    received_cost.amount = reallocated_cost

                    received_cost.ledger_account_code = previously_allocated_cost.ledger_account_code
                    received_cost.counterparty_costcentre = sender_cc.master_code
                    received_cost.period = previously_allocated_cost.period
                    received_cost.allocation_account_code = previously_allocated_cost.allocation_account_code

                    receiving_cc.allocated_costs.append(received_cost)

                    # Update the same cost object to allocate the costs from the cost centre is was previously allocated to
                    # to the new receiving cost centre (the cost centre the cost was previously allocated to becomes the new
                    # sender cost centre
                    sent_cost = Cost()
                    sent_cost.cost_hierarchy = level -1
                    sent_cost.amount = reallocated_cost * -1.0

                    sent_cost.ledger_account_code = previously_allocated_cost.ledger_account_code
                    sent_cost.period = previously_allocated_cost.period
                    sent_cost.allocation_account_code = previously_allocated_cost.allocation_account_code
                    sent_cost.counterparty_costcentre = receiving_cc.master_code

                    sender_cc.allocated_costs.append(sent_cost) #ToDo: Check

                    assert sent_cost.cost_hierarchy >= 1, "Cost hierarchy level is {}".format(sent_cost.cost_hierarchy)

    # ToDo: Implement test that ensures that the allocation is net flat (need to update below to include levels)
    # for cc in sender_costcentres:
    #     total_direct_costs = sum([cost.amount for cost in cc.direct_costs])
    #     total_allocated_costs = sum([cost.amount for cost in cc.allocated_costs if cost.cost_hierarchy==level-1])
    #     print abs(float(total_direct_costs)+float(total_allocated_costs))
    #     assert abs(float(total_direct_costs)+float(total_allocated_costs))<r.DEFAULT_MAX_CALC_ERROR,\
    #         "Total direct costs {} not equal allocated costs {} for cc \n{}\n{}\n{}"\
    #         .format(total_direct_costs,
    #                 total_allocated_costs, cc, [cost for cost in cc.direct_costs], [cost for cost in cc.allocated_costs])

    return (sender_costcentres, receiving_costcentres)

def allocate_indirect_cost_for_period(unprocessed_costcentres):
    ''' Calculates the indirect cost allocations based on headcount

    :param unprocessed_costcentres: A list of CostCentre objects, populated with headcount and direct cost information
    :return:
    '''

    processed_costcentres = []

    # Iterate through each hierarchy level and allocate the costs to the cost centres on the hierarchy level above
    # L1 is excluded as this is the final destination for all allocated costs
    hierarchy_levels = list(set([cc.hierarchy_tier for cc in unprocessed_costcentres if cc.hierarchy_tier != 1]))
    hierarchy_levels.sort()

    while hierarchy_levels: # Iterate through all the hierarchy levels from the highest number upwards
        hierarchy_level = hierarchy_levels.pop()

        # Costs are allocated from lower tiers (with a higher tier number), upwards to tiers above it
        # e.g. Tier 3 cost centres allocate costs to all Tier 1 and Tier 2 cost centres
        sender_costcentres = [cc for cc in unprocessed_costcentres if cc.hierarchy_tier == hierarchy_level]
        receiving_costcentres = [cc for cc in unprocessed_costcentres if cc.hierarchy_tier < hierarchy_level]

        alloc_percentages = get_allocation_percentages_for_hierarchy_level(costcentres=unprocessed_costcentres,
                                                                           hierarchy_level_to_allocate=hierarchy_level)

        # Allocate the direct costs of the sender cost centres based on the allocation percentages
        sender_costcentres, receiving_costcentres = allocate_dir_costs_for_tier(sender_costcentres=sender_costcentres,
                                                                                receiving_costcentres=receiving_costcentres,
                                                                                alloc_percentages=alloc_percentages,
                                                                                level=hierarchy_level)
        # Where the sender cost centres have had costs allocated to them from a previous allocation cycle, these
        # need to be allocated onwards to the receiving cost centres so that the sender cost centres are still
        # net nil
        sender_costcentres, receiving_costcentres = reallocate_previously_allocated_costs(sender_costcentres=sender_costcentres,
                                                                                          receiving_costcentres=receiving_costcentres,
                                                                                          alloc_percentages=alloc_percentages,
                                                                                          level=hierarchy_level)
        # Once a cost centre has been a "sender" cost centre, it should be net flat and does not need to be
        # re-allocated
        processed_costcentres = processed_costcentres + sender_costcentres
        unprocessed_costcentres = receiving_costcentres[:]

    all_costcentres = processed_costcentres + unprocessed_costcentres

    return all_costcentres

### Data Upload

def upload_allocated_costs_actuals(costcentres):
    '''

    :param costcentres: Cost centre objects populated with direct costs and indirect cost allocations
    :return:
    '''

    upload_time = datetime.datetime.now()   # Create timestamp

    session = db_sessionmaker()

    for cc in costcentres:
        for cost in cc.allocated_costs:

            row = TableAllocationsData(
                                        DateAllocationsRun = upload_time,
                                        SendingCostCentre = cost.counterparty_costcentre,
                                        ReceivingCostCentre = cc.master_code,
                                        SendingCompany = r.COMPANY_CODE_MAINCO, # ToDo: Refactor to make this dynamic
                                        ReceivingCompany = r.COMPANY_CODE_MAINCO, # ToDo: Refactor to make this dynamic
                                        Period = cost.period,
                                        GLAccount = cost.ledger_account_code,
                                        CostHierarchy = cost.cost_hierarchy,
                                        Value = round(cost.amount,3)    # Rounded as database field is configured as decimal
                                        )
            session.add(row)

    session.commit()
    session.close()

def upload_allocated_costs_budget(costcentres, label):
    '''

    :param costcentres: Cost centre objects populated with direct costs and indirect cost allocations
    :return:
    '''

    upload_time = datetime.datetime.now()   # Create timestamp

    session = db_sessionmaker()

    for cc in costcentres:
        for cost in cc.allocated_costs:

            row = TableBudgetAllocationsData(
                                        DateAllocationsRun = upload_time,
                                        SendingCostCentre = cost.counterparty_costcentre,
                                        ReceivingCostCentre = cc.master_code,
                                        SendingCompany = r.COMPANY_CODE_MAINCO, # ToDo: Refactor to make this dynamic
                                        ReceivingCompany = r.COMPANY_CODE_MAINCO, # ToDo: Refactor to make this dynamic
                                        Period = cost.period,
                                        GLAccount = cost.ledger_account_code,
                                        CostHierarchy = cost.cost_hierarchy,
                                        Value = round(cost.amount,3),    # Rounded as database field is configured as decimal
                                        Label = label
                                        )
            session.add(row)

    session.commit()
    session.close()

### Main Allocation Functions

def allocate_actuals_data(year, month):
    ''' Allocated direct costs based on headcount for a given period and uploads the results to the database

    :param year:
    :param month:
    :return:
    '''

    # Perform validation checks on the data before proceeding with processing
    utils.data_integrity.master_data_integrity_check_actuals(year=year, month=month)
    utils.data_integrity.check_table_has_records_for_period(year=year, month=month, table=TableFinancialStatements)

    # Get a list of cost centres populated with headcount and costs per hierarchy level
    unprocessed_costcentres = get_populated_costcentres_actuals(year=year, month=month)

    processed_costcentres = allocate_indirect_cost_for_period(unprocessed_costcentres=unprocessed_costcentres)

    utils.misc_functions.delete_table_data_for_period(table=TableAllocationsData, year=year, month=month)
    upload_allocated_costs_actuals(costcentres=processed_costcentres)

def allocation_date_check(test_year, test_month, max_year, max_month):
    '''

    :param test_year:
    :param test_month:
    :param max_year:
    :param max_month:
    :return:
    '''

    date_limit = datetime.datetime(year=max_year, month=max_month,day=1)
    current_date = datetime.datetime(year=test_year, month=test_month, day=1)
    return current_date<=date_limit

def allocate_budget_data(label, max_year=9999, max_month=13):
    ''' Creates cost allocation data for budget data for a certain budget dataset

    :param label: The tag given to the budget dataset
    :return:
    '''
    utils.data_integrity.master_data_integrity_check_budget()

    # Get a list of all periods in the Budget data in the format (year, month)
    all_periods = get_all_budget_periods(label=label)
    all_processed_costcentres = []

    for year, month in all_periods:
        # To prevent large volumes of unnecessary data being generated, the period over which allocations
        # are run can be limited by the user
        if allocation_date_check(max_year=max_year,max_month=max_month,test_year=year, test_month=month):
            unprocessed_costcentres = get_populated_costcentres_budget(year=year, month=month, label=label)
            processed_costcentres = allocate_indirect_cost_for_period(unprocessed_costcentres=unprocessed_costcentres)
            all_processed_costcentres += processed_costcentres
        else:
            break
    # Delete previously allocated data (for the relevant period only)
    session = db_sessionmaker()
    session.query(TableBudgetAllocationsData) \
        .filter(TableBudgetAllocationsData.Label == label) \
        .delete()
    session.commit()
    session.close()

    # Upload new data
    upload_allocated_costs_budget(costcentres=all_processed_costcentres, label=label)
