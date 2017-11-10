-- phpMyAdmin SQL Dump
-- version 4.5.4.1deb2ubuntu2
-- http://www.phpmyadmin.net
--
-- Host: localhost
-- Generation Time: Nov 10, 2017 at 08:07 AM
-- Server version: 5.7.20-0ubuntu0.16.04.1
-- PHP Version: 7.0.22-0ubuntu0.16.04.1

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `financial-reporting-schema`
--

-- --------------------------------------------------------

--
-- Table structure for table `tbl_DATA_allocations_actuals`
--

CREATE TABLE `tbl_DATA_allocations_actuals` (
  `ID` int(11) NOT NULL,
  `DateAllocationsRun` datetime NOT NULL COMMENT 'Timestamp of when the allocation process was run',
  `SendingCostCentre` text NOT NULL COMMENT 'Cost Centre the costs are allocated from',
  `ReceivingCostCentre` text NOT NULL COMMENT 'Cost Centre the costs are allocated to',
  `SendingCompany` int(11) NOT NULL,
  `ReceivingCompany` int(11) NOT NULL,
  `Period` datetime NOT NULL,
  `GLAccount` int(11) NOT NULL COMMENT 'Indirect cost account used for the allocation',
  `CostHierarchy` int(11) NOT NULL COMMENT 'The hierarchy tier that the costs were allocated from',
  `Value` decimal(10,3) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_DATA_allocations_budget`
--

CREATE TABLE `tbl_DATA_allocations_budget` (
  `ID` int(11) NOT NULL,
  `DateAllocationsRun` datetime NOT NULL COMMENT 'Timestamp of when the allocation process was run',
  `SendingCostCentre` text NOT NULL COMMENT 'Cost Centre the costs are allocated from',
  `ReceivingCostCentre` text NOT NULL COMMENT 'Cost Centre the costs are allocated to',
  `SendingCompany` int(11) NOT NULL,
  `ReceivingCompany` int(11) NOT NULL,
  `Period` datetime NOT NULL,
  `GLAccount` int(11) NOT NULL COMMENT 'Indirect cost account used for the allocation',
  `CostHierarchy` int(11) NOT NULL COMMENT 'The hierarchy tier that the costs were allocated from',
  `Value` decimal(10,3) NOT NULL,
  `Label` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_DATA_converted_actuals`
--

CREATE TABLE `tbl_DATA_converted_actuals` (
  `ID` int(11) NOT NULL,
  `TimeStamp` datetime DEFAULT NULL COMMENT 'Datetime the data was imported',
  `CompanyCode` int(11) NOT NULL,
  `CostCentreCode` text,
  `Period` datetime NOT NULL,
  `AccountCode` int(11) NOT NULL COMMENT 'The ledger account code',
  `Value` decimal(10,3) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_DATA_extract_finmodel`
--

CREATE TABLE `tbl_DATA_extract_finmodel` (
  `ID` int(11) NOT NULL,
  `TimeStamp` datetime NOT NULL COMMENT 'Datetime when the data was generated in the model',
  `Period` date NOT NULL COMMENT 'Period of the Budget the data relates to',
  `CompanyCode` text NOT NULL COMMENT 'Code of the company',
  `CostCentreCode` text NOT NULL COMMENT 'Code of the cost centre',
  `GLCode` int(11) NOT NULL COMMENT 'Code of the GL',
  `Value` decimal(10,0) NOT NULL,
  `Label` text NOT NULL COMMENT 'Identifier for the dataset',
  `Comments` text NOT NULL COMMENT 'User comments for the file upload'
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COMMENT='Budget and Forecast data extracted from the Financial Model';

-- --------------------------------------------------------

--
-- Table structure for table `tbl_DATA_extract_xero`
--

CREATE TABLE `tbl_DATA_extract_xero` (
  `ID` int(11) NOT NULL COMMENT 'Auto-incremented row IDs',
  `DateExtracted` datetime NOT NULL COMMENT 'DateTime for when the extract was taken from Xero',
  `ReportName` text NOT NULL COMMENT 'The name of the report as defined in Xero',
  `CompanyName` text NOT NULL COMMENT 'The company name as defined in the xero extract',
  `CostCentreName` text COMMENT 'The name of the cost centre as defined in Xero',
  `AccountCode` text NOT NULL COMMENT 'The ID mapped to the account by Xero',
  `AccountName` text NOT NULL COMMENT 'The name of the account as defined in Xero',
  `Period` datetime NOT NULL COMMENT 'The accounting period the item is posted in',
  `Value` decimal(10,3) NOT NULL COMMENT 'Balance of the account at the reporting date'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_DATA_headcount_actuals`
--

CREATE TABLE `tbl_DATA_headcount_actuals` (
  `EmployeeID` int(11) NOT NULL,
  `FirstName` text NOT NULL,
  `LastName` text NOT NULL,
  `JobTitle` text NOT NULL,
  `IsContractor` tinyint(1) NOT NULL COMMENT 'Flag for whether the headcount is a contractor or not',
  `StartDate` datetime NOT NULL COMMENT 'Date the employee started with the company',
  `EndDate` datetime DEFAULT NULL COMMENT 'Date the employee left the company',
  `CostCentreCode` text NOT NULL COMMENT 'Clearmatics ID for the cost centre the employee works in',
  `CompanyCode` int(11) NOT NULL COMMENT 'The code of the company the employee works for',
  `FTE` decimal(10,0) NOT NULL COMMENT 'Full-time equivalent of the role'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_MASTER_allocationaccounts`
--

CREATE TABLE `tbl_MASTER_allocationaccounts` (
  `ID` int(11) NOT NULL,
  `GLCode` int(11) NOT NULL,
  `GLName` text NOT NULL,
  `L2Hierarchy` text NOT NULL COMMENT 'The hierarchy node that the indirect allocation relates to',
  `L0Code` text NOT NULL,
  `L0Name` text NOT NULL,
  `L1Code` text NOT NULL,
  `L1Name` text NOT NULL,
  `L2Code` text NOT NULL,
  `L2Name` text NOT NULL,
  `L3Code` text NOT NULL,
  `L3Name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_MASTER_chartofaccounts`
--

CREATE TABLE `tbl_MASTER_chartofaccounts` (
  `ID` int(11) NOT NULL,
  `GLCode` int(11) NOT NULL,
  `GLName` varchar(255) CHARACTER SET utf8mb4 NOT NULL,
  `XeroCode` text CHARACTER SET utf8 NOT NULL COMMENT 'Code of the account in Xero',
  `XeroName` varchar(255) CHARACTER SET utf8mb4 NOT NULL COMMENT 'Description of the account in Xero',
  `L3Code` text CHARACTER SET utf8mb4 NOT NULL COMMENT 'The code for the hierarchy Level 1',
  `L3Name` text CHARACTER SET utf8mb4 NOT NULL COMMENT 'The description of the hierarchy Level 1',
  `XeroMultiplier` int(11) NOT NULL COMMENT 'Factor to convert Xero output into debits/credits'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_MASTER_companies`
--

CREATE TABLE `tbl_MASTER_companies` (
  `ID` int(11) NOT NULL,
  `XeroName` text NOT NULL COMMENT 'Name of the entity in Xero',
  `CompanyName` text NOT NULL,
  `CompanyCode` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_MASTER_costcentres`
--

CREATE TABLE `tbl_MASTER_costcentres` (
  `ID` int(11) NOT NULL,
  `XeroName` text NOT NULL COMMENT 'The text description used in Xero for the cost centre',
  `XeroCode` text NOT NULL COMMENT 'The alphanumeric code used for the tracking category',
  `CostCentreName` text NOT NULL,
  `CostCentreCode` text NOT NULL,
  `AllocationTier` int(11) NOT NULL COMMENT 'Descending tier that determines which costs are allocated in what order'
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_MASTER_nodehierarchy`
--

CREATE TABLE `tbl_MASTER_nodehierarchy` (
  `ID` int(11) NOT NULL,
  `L0Code` text NOT NULL,
  `L0Name` text NOT NULL,
  `L1Code` text NOT NULL,
  `L1Name` text NOT NULL,
  `L2Code` text NOT NULL,
  `L2Name` text NOT NULL,
  `L3Code` text NOT NULL,
  `L3Name` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_MASTER_periods`
--

CREATE TABLE `tbl_MASTER_periods` (
  `ID` int(11) NOT NULL,
  `Period` date NOT NULL,
  `IsLocked` tinyint(1) NOT NULL COMMENT 'Whether the date can be written to or not',
  `IsPublished` tinyint(1) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_OUTPUT_consolidated_actuals`
--

CREATE TABLE `tbl_OUTPUT_consolidated_actuals` (
  `ID` int(11) NOT NULL,
  `Period` datetime NOT NULL,
  `CompanyCode` int(11) NOT NULL,
  `CompanyName` text NOT NULL,
  `PartnerCompanyCode` int(11) DEFAULT NULL,
  `PartnerCompanyName` text,
  `CostCentreCode` text,
  `CostCentreName` text,
  `PartnerCostCentreCode` text,
  `PartnerCostCentreName` text,
  `FinancialStatement` text NOT NULL,
  `GLAccountCode` int(11) NOT NULL,
  `GLAccountName` text NOT NULL,
  `L1Code` text NOT NULL,
  `L1Name` text NOT NULL,
  `L2Code` text NOT NULL,
  `L2Name` text NOT NULL,
  `L3Code` text NOT NULL,
  `L3Name` text NOT NULL,
  `CostHierarchyNumber` int(11) DEFAULT NULL,
  `Value` decimal(15,3) NOT NULL,
  `TimeStamp` datetime NOT NULL,
  `Label` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

-- --------------------------------------------------------

--
-- Table structure for table `tbl_OUTPUT_consolidated_budget`
--

CREATE TABLE `tbl_OUTPUT_consolidated_budget` (
  `ID` int(11) NOT NULL,
  `Period` datetime NOT NULL,
  `CompanyCode` int(11) NOT NULL,
  `CompanyName` text NOT NULL,
  `PartnerCompanyCode` int(11) DEFAULT NULL,
  `PartnerCompanyName` text,
  `CostCentreCode` text,
  `CostCentreName` text,
  `PartnerCostCentreCode` text,
  `PartnerCostCentreName` text,
  `FinancialStatement` text NOT NULL,
  `GLAccountCode` int(11) NOT NULL,
  `GLAccountName` text NOT NULL,
  `L1Code` text NOT NULL,
  `L1Name` text NOT NULL,
  `L2Code` text NOT NULL,
  `L2Name` text NOT NULL,
  `L3Code` text NOT NULL,
  `L3Name` text NOT NULL,
  `CostHierarchyNumber` int(11) DEFAULT NULL,
  `Value` decimal(15,3) NOT NULL,
  `TimeStamp` datetime NOT NULL,
  `Label` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `tbl_DATA_allocations_actuals`
--
ALTER TABLE `tbl_DATA_allocations_actuals`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_DATA_allocations_budget`
--
ALTER TABLE `tbl_DATA_allocations_budget`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_DATA_converted_actuals`
--
ALTER TABLE `tbl_DATA_converted_actuals`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_DATA_extract_finmodel`
--
ALTER TABLE `tbl_DATA_extract_finmodel`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_DATA_extract_xero`
--
ALTER TABLE `tbl_DATA_extract_xero`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_DATA_headcount_actuals`
--
ALTER TABLE `tbl_DATA_headcount_actuals`
  ADD PRIMARY KEY (`EmployeeID`);

--
-- Indexes for table `tbl_MASTER_allocationaccounts`
--
ALTER TABLE `tbl_MASTER_allocationaccounts`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_MASTER_chartofaccounts`
--
ALTER TABLE `tbl_MASTER_chartofaccounts`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_MASTER_companies`
--
ALTER TABLE `tbl_MASTER_companies`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_MASTER_costcentres`
--
ALTER TABLE `tbl_MASTER_costcentres`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_MASTER_nodehierarchy`
--
ALTER TABLE `tbl_MASTER_nodehierarchy`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_MASTER_periods`
--
ALTER TABLE `tbl_MASTER_periods`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_OUTPUT_consolidated_actuals`
--
ALTER TABLE `tbl_OUTPUT_consolidated_actuals`
  ADD PRIMARY KEY (`ID`);

--
-- Indexes for table `tbl_OUTPUT_consolidated_budget`
--
ALTER TABLE `tbl_OUTPUT_consolidated_budget`
  ADD PRIMARY KEY (`ID`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `tbl_DATA_allocations_actuals`
--
ALTER TABLE `tbl_DATA_allocations_actuals`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_DATA_allocations_budget`
--
ALTER TABLE `tbl_DATA_allocations_budget`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_DATA_converted_actuals`
--
ALTER TABLE `tbl_DATA_converted_actuals`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_DATA_extract_finmodel`
--
ALTER TABLE `tbl_DATA_extract_finmodel`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_DATA_extract_xero`
--
ALTER TABLE `tbl_DATA_extract_xero`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT COMMENT 'Auto-incremented row IDs';
--
-- AUTO_INCREMENT for table `tbl_MASTER_allocationaccounts`
--
ALTER TABLE `tbl_MASTER_allocationaccounts`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_MASTER_chartofaccounts`
--
ALTER TABLE `tbl_MASTER_chartofaccounts`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_MASTER_companies`
--
ALTER TABLE `tbl_MASTER_companies`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_MASTER_costcentres`
--
ALTER TABLE `tbl_MASTER_costcentres`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_MASTER_nodehierarchy`
--
ALTER TABLE `tbl_MASTER_nodehierarchy`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_MASTER_periods`
--
ALTER TABLE `tbl_MASTER_periods`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_OUTPUT_consolidated_actuals`
--
ALTER TABLE `tbl_OUTPUT_consolidated_actuals`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
--
-- AUTO_INCREMENT for table `tbl_OUTPUT_consolidated_budget`
--
ALTER TABLE `tbl_OUTPUT_consolidated_budget`
  MODIFY `ID` int(11) NOT NULL AUTO_INCREMENT;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
