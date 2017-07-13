#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains constants and other references used by the script
'''

### Time Constraints

# Simple checks used to validate input before making a database request to check whether the date is in the database
AVAILABLE_PERIODS_YEARS = [2017,2018,2019,2020]
AVAILABLE_PERIODS_MONTHS = [1,2,3,4,5,6,7,8,9,10,11,12]

### Master Data Mappings

COMPANY_CODE_CLEARMATICS = 1000

# Xero data mappings

XERO_DATA_BALANCESHEET = "BalanceSheet"
XERO_DATA_INCOMESTATEMENT = "ProfitAndLoss"

# Clearmatics data mappings

CM_DATA_BALANCESHEET = "BalanceSheet"
CM_DATA_INCOMESTATEMENT = "IncomeStatement"
CM_IS_L2_DEPRECIATION = 'L2-DEP'
CM_IS_L2_DEFTAXES = 'L2-TAXDEF'


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
                   'L2L-OTHER-ST']

CM_BS_L2_INVESTMENT = ['L2A-PPE']
CM_BS_L2_FINANCING = ['L2L-DEBT-ST', 'L2L-DEBT-LT', 'L2E-SHAREPREM', 'L2E-PREF', 'L2E-COMMON']
CM_BS_L2_EXCLUDED = ['L2A-CASH', 'L2E-RETEARN']

CM_CF_GL_OPERATING = 900010
CM_CF_GL_INVESTMENT = 900020
CM_CF_GL_FINANCING = 900030

### Output Constants

DEFAULT_OUTPUT_FOLDERNAME = "fin-data-output"
DEFAULT_OUTPUT_FOLDERPATH = "..[CURRENT DIRECTORY]/" + DEFAULT_OUTPUT_FOLDERNAME

### Financial Constants

ALLOCATIONS_MAX_ERROR = 0.0001

### Database Constants

TBL_DATA_XEROEXTRACT = "tbl_DATA_xeroextract"
COL_XEROEXTRACT_ACCOUNTCODE = "AccountCode"

TBL_MASTER_PERIODS = "tbl_MASTER_periods"
COL_PERIOD_PERIOD = "Period"

TBL_MASTER_COSTCENTRES = "tbl_MASTER_costcentres"
COL_CC_CLEARMATICSCODE = "ClearmaticsCode"

TBL_MASTER_COMPANIES = "tbl_MASTER_companies"
COL_COMPANIES_CLEARMATICSCODE = "ClearmaticsCode"

TBL_DATA_FINANCIALSTATEMENTS = "tbl_DATA_financialstatements"

TBL_MASTER_HEADCOUNT = "tbl_MASTER_headcount"
COL_HEADCOUNT_COSTCENTRE = "CostCentre"

TBL_MASTER_CHARTOFACCOUNTS = "tbl_MASTER_chartofaccounts"
COL_CHARTACC_XEROCODE = "XeroCode"
COL_CHARTACC_CLEARMATICSCODE = "ClearmaticsCode"

TBL_MASTER_ALLOCACCOUNTS = "tbl_MASTER_allocationaccounts"
COL_ALLOCACC_CODE = "ClearmaticsCode"

TBL_DATA_ALLOCATIONS = "tbl_DATA_allocations"

TBL_OUTPUT_CONSOL_FINSTAT = "tbl_OUTPUT_consolidated_finstat"

TBL_MASTER_NODEHIERARCHY = "tbl_MASTER_nodehierarchy"
COL_NODE_L3CODE = "L3Code"