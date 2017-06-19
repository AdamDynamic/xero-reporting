
# Management Reporting Database

The purpose of this module is to generate a standardised set of company financial data that can be used for management reporting purposes. 

## Command Line Interface

The management reporting tool uses a command line interface to control the import, processing and output of financial data. The commands below are available for the `main.py` module. Note that the `--help` function works for all commands in the interface.

`get_xero_data`

Retrieves financial data from the company Xero instance and imports it into the database

`convert_xero_data`

Re-maps the imported Xero reporting data to standardised internal company master data mappings. 

`run_allocations`

Runs the cost allocation process on the direct costs of support functions.

`create_consolidated_table`

Creates a user-readable Income Statement that combines both the Xero data (converted to Clearmatics master data mappings) and the allocated cost data. 

This is the final dataset that can be used for management reporting.

`set_period_lock`

A period lock is enabled in the database to mitigate the risk that previously reported data is accidently changed. If a period is locked, commands that transform the data will return an error message.

To make changes in a locked period, the period must first be unlocked by setting locked flag as False: `--locked=False`

`status`

Outputs a table to the console summarising which steps in the end-to-end process have been completed and whether the data in upstream processes is up to date. 


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
 - Telecoms (e.g. the cost of the phones, the fibre, etc)
 - The company Slack subscription



## Allocations

The operational costs of cost centres below Level 1 are allocated upwards sequentially, starting with the lowest level.

e.g.

Level 3 allocates costs to Level 1 _and_ Level 2

Level 2 allocates costs (both direct costs and indirect costs allocated to Level 2 by Level 3) to Level 1 only

Level 1 does not allocate any of its direct or indirect costs. 

*Costs are allocated based on the headcount of the receiving cost centres*. For example, if a L2 cost centre was allocating its costs to two L1 cost centres that had 3 and 7 heads respectively, the first L1 cost centre would receive 30% of the L2's costs, and the second L1 cost centre would receive the remaining 70%.
