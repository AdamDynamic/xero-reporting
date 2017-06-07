'''
Main control point for the module

Purpose of the module is to output financial reporting data
'''


def get_xero_data():
    pass

def output_graph_images():
    pass

# CUI commands

# Get Xero data (with date range) [-c xero -o pull]

# Calculate allocations [-c allocations -o calculate]

# Create new period (copy forwards headcount data?) [-c period -o create]

# Delete data from [reporting table, allocation table, xero table] - specify date range [-c delete -o table_name -p 2017.03]

# Push allocations to reporting table [ -c allocations -o push]

# Lock/unlock periods [-c period -o lock/unlock]

# Validate data (check all fields in master data vs. imported data, etc) [-o data -c validate]
#   - Check that all line items have a cost centre mapped to them
#   - Check that all cost centres are contained in the master data tables

# Print summary table (for quickly checking vs. Xero) [-o data -c summary]

# Output back-up [-o data -c backup]


## Management Reporting

# 1) Extract financial reporting data

# 2) Map the data against master data to produce a standardised data set

# 3) Perform required transformations on data (allocations, etc)

# 4) Remove any previously published data from reporting database

# 5) Save transformed data to reporting database

# 6) Generate pdf report of data?

## Forecasting

# 1) Extract financial data (from reporting database or from xero?)

# 2)


# 2) Parse the data to extract what is required

# 3) Process the data into graphical format

# 4) Output the graphs to a readable format

# keen.io provide templates for dashboards
# also looker and segment