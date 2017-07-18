#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains the database table objects created to support the SQLAlchemy ORM mappings. Each table in the primary
database is represented by a mapping object here.
'''

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

import references as r

Base = declarative_base()

class TableXeroExtract(Base):
    '''
    SQLAlchemy ORM class for the tbl_DATA_xeroextract table
    '''

    __tablename__ = r.TBL_DATA_XEROEXTRACT

    ID = Column(Integer, primary_key=True)
    DateExtracted = Column(DateTime)
    ReportName = Column(String)
    CompanyName = Column(String)
    CostCentreName = Column(String, nullable=True)
    AccountCode = Column(String)
    AccountName = Column(String)
    Period = Column(DateTime)
    Value = Column(Float)

    def __repr__(self):
        return "< {}: Name: {}," \
               " DateExtracted: {}," \
               " CompanyName: {}," \
               " CostCentreName: {}," \
               " AccountCode: {}," \
               " AccountName: {}," \
               " Period: {}," \
               " Value: {} >".format(r.TBL_DATA_XEROEXTRACT,
                                     self.ReportName,
                                     self.DateExtracted,
                                     self.CompanyName,
                                     self.CostCentreName,
                                     self.AccountCode,
                                     self.AccountName,
                                     self.Period,
                                     self.Value)


class TablePeriods(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_periods table
    '''

    __tablename__ = r.TBL_MASTER_PERIODS

    ID = Column(Integer, primary_key=True)
    Period = Column(DateTime)
    IsLocked = Column(Integer) # Boolean check whether the period is locked or not

    def __repr__(self):
        return "< {}: " \
               " Period: {}," \
               " IsLocked: {} >".format(r.TBL_MASTER_PERIODS, self.Period, self.IsLocked)


class TableCostCentres(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_costcentres table
    '''

    __tablename__ = r.TBL_MASTER_COSTCENTRES

    ID = Column(Integer, primary_key=True)
    XeroName = Column(String)
    XeroCode = Column(String)
    CostCentreName = Column(String)
    CostCentreCode = Column(String)
    AllocationTier = Column(Integer)


class TableCompanies(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_companies table
    '''

    __tablename__ = r.TBL_MASTER_COMPANIES

    ID = Column(Integer, primary_key=True)
    XeroName = Column(String)
    CompanyName = Column(String)
    CompanyCode = Column(Integer)


class TableFinancialStatements(Base):
    '''
    SQLAlchemy ORM class for the tbl_DATA_financialstatements table
    '''

    __tablename__ = r.TBL_DATA_FINANCIALSTATEMENTS

    ID = Column(Integer, primary_key=True)
    TimeStamp = Column(DateTime)
    CompanyCode = Column(Integer, ForeignKey(r.TBL_MASTER_COMPANIES + "." + r.COL_COMPANIES_COMPCODE))
    CostCentreCode = Column(String, ForeignKey(r.TBL_MASTER_COSTCENTRES + "." + r.COL_CC_CODE), nullable=True)
    Period = Column(DateTime)
    AccountCode = Column(Integer, ForeignKey(r.TBL_MASTER_CHARTOFACCOUNTS + "." + r.COL_CHARTACC_GLCODE))
    Value = Column(Float)

    def __repr__(self):
        return "<" \
               "ID: {}, " \
               "TimeStamp: {}, " \
               "CompanyCode: {}, " \
               "CostCentreCode: {}, " \
               "Period: {}, " \
               "AccountCode: {}, " \
               "Value: {}, " \
               ">".format(self.ID,
                          self.TimeStamp,
                          self.CompanyCode,
                          self.CostCentreCode,
                          self.Period,
                          self.AccountCode,
                          self.Value)


class TableHeadcount(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_headcount table
    '''

    __tablename__ = r.TBL_MASTER_HEADCOUNT

    EmployeeID = Column(Integer, primary_key=True)
    FirstName = Column(String)
    LastName = Column(String)
    JobTitle = Column(String)
    StartDate = Column(DateTime)
    EndDate = Column(DateTime, nullable=True)
    CostCentreCode = Column(String, ForeignKey(r.TBL_MASTER_COSTCENTRES + "." + r.COL_CC_CODE))
    CompanyCode = Column(String, ForeignKey(r.TBL_MASTER_COMPANIES +"." + r.COL_COMPANIES_COMPCODE))


class TableChartOfAccounts(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_chartofaccounts table
    '''

    __tablename__ = r.TBL_MASTER_CHARTOFACCOUNTS

    ID = Column(Integer, primary_key=True)
    GLCode = Column(Integer)
    GLName = Column(String)
    XeroCode = Column(String)
    XeroName = Column(String)
    L3Code = Column(String)
    L3Name = Column(String)
    XeroMultiplier = Column(Integer)


class TableAllocationAccounts(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_allocationaccounts table
    '''

    __tablename__ = r.TBL_MASTER_ALLOCACCOUNTS

    ID = Column(Integer, primary_key=True)
    GLCode = Column(Integer)
    GLName = Column(String)
    L2Hierarchy = Column(String)
    L0Code = Column(String)
    L0Name = Column(String)
    L1Code = Column(String)
    L1Name = Column(String)
    L2Code = Column(String)
    L2Name = Column(String)
    L3Code = Column(String)
    L3Name = Column(String)


class TableAllocationsData(Base):
    '''
    SQLAlchemy ORM class for the tbl_DATA_allocations table
    '''

    __tablename__ = r.TBL_DATA_ALLOCATIONS

    ID = Column(Integer, primary_key=True)
    DateAllocationsRun = Column(DateTime)
    SendingCostCentre = Column(String, ForeignKey(r.TBL_MASTER_COSTCENTRES +"." + r.COL_CC_CODE))
    ReceivingCostCentre = Column(String, ForeignKey(r.TBL_MASTER_COSTCENTRES +"." + r.COL_CC_CODE))
    SendingCompany = Column(Integer, ForeignKey(r.TBL_MASTER_COMPANIES +"." + r.COL_COMPANIES_COMPCODE))
    ReceivingCompany = Column(Integer, ForeignKey(r.TBL_MASTER_COMPANIES +"." + r.COL_COMPANIES_COMPCODE))
    Period = Column(DateTime)
    GLAccount = Column(Integer)
    CostHierarchy = Column(Integer)
    Value = Column(Float)


class TableConsolidatedFinStatements(Base):
    '''
    SQLAlchemt ORM class for the tbl_OUTPUT_consolidated_is table
    '''

    __tablename__ = r.TBL_OUTPUT_CONSOL_FINSTAT

    ID = Column(Integer, primary_key=True)
    Period = Column(DateTime)
    CompanyCode = Column(Integer)
    CompanyName = Column(String)
    PartnerCompanyCode = Column(Integer, nullable=True)
    PartnerCompanyName = Column(String, nullable=True)
    CostCentreCode = Column(String, nullable=True)
    CostCentreName = Column(String, nullable=True)
    PartnerCostCentreCode = Column(String, nullable=True)
    PartnerCostCentreName = Column(String, nullable=True)
    FinancialStatement = Column(String)
    GLAccountCode = Column(Integer)
    GLAccountName = Column(String)
    L1Code = Column(String)
    L1Name = Column(String)
    L2Code = Column(String)
    L2Name = Column(String)
    L3Code = Column(String)
    L3Name = Column(String)
    CostHierarchyNumber = Column(Integer, nullable=True)
    Value = Column(Float)
    TimeStamp = Column(DateTime)

    def __repr__(self):
        return "<ID: {}, " \
               "Period: {}, " \
               "CompCode: {}, " \
               "CompName: {}, " \
               "PartCompCode: {}, " \
               "PartCompName: {}, " \
               "CostCenCode: {}, " \
               "CostCenName: {}, " \
               "PartCostCenCode: {}, " \
               "PartCostCenName: {}, " \
               "FinStat: {}, " \
               "GLCode: {}, " \
               "GLName: {}, " \
               "L1Code: {}, " \
               "L1Name: {}, " \
               "L2Code: {}, " \
               "L2Name: {}, " \
               "L3Code: {}, " \
               "L3Name: {}, " \
               "CostHierNo: {}, " \
               "Value: {}, " \
               "TimeStamp: {}>"\
            .format(self.ID,
                    self.Period,
                    self.CompanyCode,
                    self.CompanyName,
                    self.PartnerCompanyCode,
                    self.PartnerCompanyName,
                    self.CostCentreCode,
                    self.CostCentreName,
                    self.PartnerCostCentreCode,
                    self.PartnerCostCentreName,
                    self.FinancialStatement,
                    self.GLAccountCode,
                    self.GLAccountName,
                    self.L1Code,
                    self.L1Name,
                    self.L2Code,
                    self.L2Name,
                    self.L3Code,
                    self.L3Name,
                    self.CostHierarchyNumber,
                    self.Value,
                    self.TimeStamp
                    )


class TableNodeHierarchy(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_nodehierarchy table
    '''

    __tablename__ = r.TBL_MASTER_NODEHIERARCHY

    ID = Column(Integer, primary_key=True)
    L0Code = Column(String)
    L0Name = Column(String)
    L1Code = Column(String)
    L1Name = Column(String)
    L2Code = Column(String)
    L2Name = Column(String)
    L3Code = Column(String)
    L3Name = Column(String)


