
# Management Reporting Database

The purpose of this repo is to generate a standardised set of company financial data that can be used for management reporting purposes by users of Xero.

## Command Line Interface

The management reporting tool uses a command line interface to control the import, processing and output of financial data. The commands below are available for the `main.py` module.

Note also that the `--help` function works for all commands in the interface.

### Creating Reporting Data

To create a valid dataset the commands below must be run *in order*. It is recommended that the output for each stage be checked before the next stage is processed:

1. `get_xero_data`

Retrieves financial data from the company Xero instance and imports it into the database. Options are `--year` and `--month` to set the period you want to pull into the database.

2. `convert_xero_data`

Re-maps the imported Xero reporting data to standardised internal company master data mappings. Options are `--year` and `--month` to set the period you want to convert.

3. `run_allocations`

Runs the cost allocation process on the direct costs of support functions. Options are `--year` and `--month` to set the period you want to run allocations on.

4. `create_consolidated_table`

Creates a user-readable Income Statement that combines both the Xero data (converted to master data mappings of the user company) and the allocated cost data. Options are `--year` and `--month` to set the period you want to create the consolidated table for.

Once `get_xero_data`, `convert_xero_data`, `run_allocations` and `create_consolidated_table` have been run (*in that order*) then the data is ready to be reported on. See the `status` function below for user visibility on whether the process has been run correctly.

### Other Functions

`set_period_lock`

A period lock is enabled in the database to mitigate the risk that previously reported data is accidently changed. If a period is locked, commands that transform the data will return an error message. Options are `--year` and `--month` to set the period you want to lock/unlock and `--locked` (`=True` or `=False`) to change the locking status of the period.

If a period is locked, then no other processes can be run on the period without first unlocking the period. 

`status`

Outputs a table to the console summarising which steps in the end-to-end process have been completed and whether the data in upstream processes is up to date. If the `TimeStampCheck` check shows anything other than `Pass` then some processes need to be re-run to ensure that the final dataset reflects the data held in Xero (check the error message for details).

The purpose of this check is to mitigate the risk that one step in the process is changed but that the latest data isn't subsequently pulled into the final consolidated table.

`output_to_csv`

Outputs a .csv file of the consolidated income statement to folder called `fin-data-output`. By default the file is created in the directory the `main.py` file resides in (in a sub-folder called `fin-data-output` which the script will create automatically if it doesn't already exist).

The user can specify the output file using the `--folder=/user/specified/filepath/here` flag.

## Master Data


To use the repo the user must define certain master data for the user company that Xero data is then mapped against. The purpose of re-mapping the Xero data is to accommodate instances where financial data must be mapped against a standard internal master data already in use within the company, or where data must be compared against non-Xero data and a common set of master data is used to facilitate this.


## Cost Centre Hierarchy

Each cost centre in the business has a hierarchy level. The key principle is that only those cost centres at the top of the hierarchy (Level 1) can have non-zero costs. All other levels must allocate their direct costs and previously-allocated indirect costs to cost centres in the levels above.

The hierarchy levels are defined as follows:

### Level 1

The cost centres at the top (Level 1) are the commercial focus of the business and drive the requirements for all other cost centres. Without Level 1 cost centres, the business would not exist.

### Level 2

Support functions in the business that exist to facilitate the company's commercial operations. Examples include any costs relating to the Finance or HR functions of the business.

### Level 3

Level 3 cost centres comprise of costs used by all other areas of the business. These are:
 - Rent
 - Building service charges
 - Telecoms (e.g. the cost of the telephones, the fibre, etc)
 - The company Slack subscription


## Allocations

The operational costs of cost centres below Level 1 are allocated upwards sequentially, starting with the lowest level.

e.g.

Level 3 allocates costs to Level 1 _and_ Level 2

Level 2 allocates costs (both direct costs and indirect costs allocated to Level 2 by Level 3) to Level 1 only

Level 1 does not allocate any of its direct or indirect costs. 

*Costs are allocated based on the headcount of the receiving cost centres*. For example, if a L2 cost centre was allocating its costs to two L1 cost centres that had 3 and 7 heads respectively, the first L1 cost centre would receive 30% of the L2's costs, and the second L1 cost centre would receive the remaining 70%.


## Cashflow

The Xero API does not provide any cashflow reports so instead the cashflows must be calculated from the Income Statement and Balance Sheet using the indirect method. 

This requires that the master data be correctly configured. The `references.py` file contains the relevant nodes used for the calculations of _Cashflow from Operations_, _Cashflow from Investments_ and _Cashflow from Financing_.

The calculated indirect cashflow for the period is compared to the movement in the cash balances between Balance Sheet dates to validate the calculations.

## Xero Configuration

The Cost Centres used in the model are configured as user-defined attributes in Xero and must be manually populated by users for all costs upon input into Xero. 

The user of the model must identify the Xero ID of the attribute (looks something like `70e6c91d-3de7-2947-a542-d6f1fd741be2`) and set the `XERO_UNASSIGNED_CC` variable in `references_private.py` to this value.

*Note*: The model will raise a `UnallocatedCostsNotNilError` error if the costs not assigned to a cost centre do not net to nil.

## To-Do List

The following items are still outstanding:

1. Way of efficiently updating the headcount table to account for joiners/leavers
2. Unit testing for `cashflow_calcs.py` module.
3. Include descriptions of the tables in the README file.

