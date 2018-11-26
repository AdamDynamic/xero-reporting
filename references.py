#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains constants and other references used by the script
'''

import datetime


### Time Constraints

# Simple checks used to validate input before making a database request to check whether the date is in the database
MODEL_START_DATE = datetime.datetime(year=2017, month=3, day=1) # The first period of valid data in the model
AVAILABLE_PERIODS_YEARS = [2017,2018,2019,2020]
AVAILABLE_PERIODS_MONTHS = [1,2,3,4,5,6,7,8,9,10,11,12]

### Master Data Mappings

COMPANY_CODE_MAINCO = 1000

HEADCOUNT_CODE_CONTRACTOR = "L3HC-CONT"
HEADCOUNT_CODE_PERMANENT = "L3HC-PERM"

HEADCOUNT_NAME_CONTRACTOR = "headcount-contract"
HEADCOUNT_NAME_PERMANENT = "headcount-permanent"

# Xero data mappings

XERO_DATA_BALANCESHEET = "BalanceSheet"
XERO_DATA_INCOMESTATEMENT = "ProfitAndLoss"

# Clearmatics data mappings

CM_DATA_BALANCESHEET = "BalanceSheet"
CM_DATA_INCOMESTATEMENT = "IncomeStatement"
CM_DATA_HEADCOUNT = "Headcount"

CM_IS_L2_DEPRECIATION = 'L2-DEP'
CM_IS_L2_DEFTAXES = 'L2-TAXDEF'
CM_IS_L3_NONCASHFINCHARGE = 'L3-FIN-NC'     # Used for the calculation of cash flows from financing
CM_IS_L2_FX = 'L2-FX'
CM_IS_L3_FX_DEBT = 'L3-FX-DEBT'             # Used for the calculation of cash flows from financing

CM_BS_CASH = 'L2A-CASH'

CM_HC_L1 = "L1-Headcount"
CM_HC_L2 = "L2-Headcount"
CM_HC_GL_PERMANENT = 999998
CM_HC_GL_CONTRACT = 999999 # ToDo: Refactor to capture GLs for Perm and Contract headcount

OUTPUT_LABEL_ACTUALS = "actuals"

# Balance Sheet mappings (used for calculation of cash flow)

CM_BS_L2_OPERATING = ['L2A-REC',
                   'L2A-INV',
                   'L2A-PREPAY',
                   'L2L-PAYABLE',
                   'L2A-INTREC',
                   'L2A-OTHER-ST',
                   'L2L-INTPAY',
                   'L2L-ACCRUAL',
                   'L2L-SALARY',
                   'L2L-VAT',
                   'L2L-CONSORT',
                   'L2L-OTHER-ST',
                   'L2L-OTHER-LT']

CM_BS_L2_INVESTMENT = ['L2A-PPE']
CM_BS_L2_FINANCING = ['L2L-DEBT-ST', 'L2L-DEBT-LT', 'L2E-SHAREPREM', 'L2E-PREF', 'L2E-COMMON']
CM_BS_L2_EXCLUDED = ['L2A-CASH', 'L2E-RETEARN']

CM_CF_GL_OPERATING = 900010
CM_CF_GL_INVESTMENT = 900020
CM_CF_GL_FINANCING = 900030

### Financial Constants

DEFAULT_MAX_CALC_ERROR = 0.0001 # The standard error tolerance used in the model's calculations

### Database Constants

#### Master Data

TBL_MASTER_ALLOCACCOUNTS = "tbl_MASTER_allocationaccounts"
COL_ALLOCACC_CODE = "GLCode"

TBL_MASTER_CHARTOFACCOUNTS = "tbl_MASTER_chartofaccounts"
COL_CHARTACC_XEROCODE = "XeroCode"
COL_CHARTACC_GLCODE = "GLCode"

TBL_MASTER_COMPANIES = "tbl_MASTER_companies"
COL_COMPANIES_COMPCODE = "CompanyCode"

TBL_MASTER_COSTCENTRES = "tbl_MASTER_costcentres"
COL_CC_CODE = "CostCentreCode"

TBL_MASTER_PERIODS = "tbl_MASTER_periods"
COL_PERIOD_PERIOD = "Period"
COL_PERIOD_ISLOCKED = "IsLocked"
COL_PERIOD_ISPUBLISHED = "IsPublished"

TBL_MASTER_NODEHIERARCHY = "tbl_MASTER_nodehierarchy"
COL_NODE_L3CODE = "L3Code"

#### User Data

TBL_DATA_ALLOCATIONS_ACTUALS = "tbl_DATA_allocations_actuals"

TBL_DATA_ALLOCATIONS_BUDGET = "tbl_DATA_allocations_budget"

TBL_DATA_HEADCOUNT_ACTUALS = "tbl_DATA_headcount_actuals"
COL_HEADCOUNT_COSTCENTRE = "CostCentre"

TBL_DATA_EXTRACT_FINMODEL = "tbl_DATA_extract_finmodel"

TBL_DATA_CONVERTED_ACTUALS = "tbl_DATA_converted_actuals"

TBL_DATA_EXTRACT_XERO = "tbl_DATA_extract_xero"
COL_XEROEXTRACT_ACCOUNTCODE = "AccountCode"

#### Output Data

TBL_OUTPUT_CONSOL_ACTUALS = "tbl_OUTPUT_consolidated_actuals"

TBL_OUTPUT_CONSOL_BUDGET = "tbl_OUTPUT_consolidated_budget"