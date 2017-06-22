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

### Output Constants

DEFAULT_OUTPUT_FOLDERNAME = "fin-data-output"
DEFAULT_OUTPUT_FOLDERPATH = "..[CURRENT DIRECTORY]/" + DEFAULT_OUTPUT_FOLDERNAME

### Financial Constants

ALLOCATIONS_MAX_ERROR = 0.0001

### Database Constants

TBL_DATA_XEROEXTRACT = "tbl_DATA_xeroextract"
COL_XEROEXTRACT_ACCOUNTCODE = "AccountCode"

TBL_MASTER_PERIODS = "tbl_MASTER_periods"

TBL_MASTER_COSTCENTRES = "tbl_MASTER_costcentres"
COL_CC_CLEARMATICSCODE = "ClearmaticsCode"

TBL_MASTER_COMPANIES = "tbl_MASTER_companies"
COL_COMPANIES_CLEARMATICSCODE = "ClearmaticsCode"

TBL_DATA_PROFITANDLOSS = "tbl_DATA_profitandloss"

TBL_MASTER_HEADCOUNT = "tbl_MASTER_headcount"
COL_HEADCOUNT_COSTCENTRE = "CostCentre"

TBL_MASTER_CHARTOFACCOUNTS = "tbl_MASTER_chartofaccounts"
COL_CHARTACC_XEROCODE = "XeroCode"
COL_CHARTACC_CLEARMATICSCODE = "ClearmaticsCode"

TBL_MASTER_ALLOCACCOUNTS = "tbl_MASTER_allocationaccounts"

TBL_DATA_ALLOCATIONS = "tbl_DATA_allocations"

TBL_OUTPUT_CONSOL_IS = "tbl_OUTPUT_consolidated_is"
