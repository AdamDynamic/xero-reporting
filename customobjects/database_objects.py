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

    __tablename__ = r.TBL_DATA_ALLOCATIONS_ACTUALS

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


class TableBudgetAllocationsData(Base):
    '''
    SQLAlchemy ORM class for the tbl_DATA_allocations table
    '''

    __tablename__ = r.TBL_DATA_ALLOCATIONS_BUDGET

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
    Label = Column(String)


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


class TableCompanies(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_companies table
    '''

    __tablename__ = r.TBL_MASTER_COMPANIES

    ID = Column(Integer, primary_key=True)
    XeroName = Column(String)
    CompanyName = Column(String)
    CompanyCode = Column(Integer)


class TableConsolidatedFinStatements(Base):
    '''
    SQLAlchemt ORM class for the tbl_OUTPUT_consolidated_is table
    '''

    __tablename__ = r.TBL_OUTPUT_CONSOL_ACTUALS

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
    Label = Column(String)

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
               "TimeStamp: {}, " \
               "Label: {}>"\
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
                    self.TimeStamp,
                    self.Label
                    )


class TableConsolidatedBudget(Base):
    '''
    SQLAlchemt ORM class for the tbl_OUTPUT_consolidated_is table
    '''

    __tablename__ = r.TBL_OUTPUT_CONSOL_BUDGET

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
    Label = Column(String)

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
               "TimeStamp: {}, " \
               "Label: {}>"\
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
                    self.TimeStamp,
                    self.Label
                    )


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


class TableFinancialStatements(Base):
    '''
    SQLAlchemy ORM class for the tbl_DATA_financialstatements table
    '''

    __tablename__ = r.TBL_DATA_CONVERTED_ACTUALS

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


class TableFinModelExtract(Base):
    '''
    SQLAlchemy ORM class for the tbl_DATA_finmodelextract table
    '''

    __tablename__ = r.TBL_DATA_EXTRACT_FINMODEL

    ID = Column(Integer, primary_key=True)
    TimeStamp = Column(DateTime)
    Period = Column(DateTime)
    CompanyCode = Column(String, ForeignKey(r.TBL_MASTER_COMPANIES +"." + r.COL_COMPANIES_COMPCODE))
    CostCentreCode = Column(String, ForeignKey(r.TBL_MASTER_COSTCENTRES +"." + r.COL_CC_CODE))
    GLCode = Column(String, ForeignKey(r.TBL_MASTER_CHARTOFACCOUNTS + "." + r.COL_CHARTACC_GLCODE))
    Value = Column(Float)
    Label = Column(String)
    Comments = Column(String)

    def _repr__(self):
        return "<ID: {}," \
               " TimeStamp: {}," \
               " Period: {}," \
               " CompanyCode: {}," \
               " CostCentreCode: {}," \
               " GLCode: {}," \
               " Value: {}," \
               " Label: {}," \
               " Comments: {}>"\
            .format(self.ID,
                    self.TimeStamp,
                    self.Period,
                    self.CompanyCode,
                    self.CostCentreCode,
                    self.GLCode,
                    self.Value,
                    self.Label,
                    self.Comments)


class TableHeadcount(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_headcount table
    '''

    __tablename__ = r.TBL_DATA_HEADCOUNT_ACTUALS

    EmployeeID = Column(Integer, primary_key=True)
    FirstName = Column(String)
    LastName = Column(String)
    JobTitle = Column(String)
    IsContractor = Column(Integer)
    StartDate = Column(DateTime)
    EndDate = Column(DateTime, nullable=True)
    CostCentreCode = Column(String, ForeignKey(r.TBL_MASTER_COSTCENTRES + "." + r.COL_CC_CODE))
    CompanyCode = Column(String, ForeignKey(r.TBL_MASTER_COMPANIES +"." + r.COL_COMPANIES_COMPCODE))
    FTE = Column(Float)

    def __repr__(self):
        return "< ID: {}," \
               " FirstName: {}," \
               " LastName: {}," \
               " JobTitle: {}," \
               " IsContractor: {},"\
               " StartDate: {}," \
               " EndDate: {}," \
               " CostCentre: {}," \
               " CompanyCode: {}," \
               " FTE: {} >"\
            .format(self.EmployeeID, self.FirstName, self.LastName, self.JobTitle, self.IsContractor,
                    self.StartDate, self.EndDate, self.CostCentreCode, self.CompanyCode, self.FTE)


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


class TablePeriods(Base):
    '''
    SQLAlchemy ORM class for the tbl_MASTER_periods table
    '''

    __tablename__ = r.TBL_MASTER_PERIODS

    ID = Column(Integer, primary_key=True)
    Period = Column(DateTime)
    IsLocked = Column(Integer)
    IsPublished = Column(Integer)


class TableXeroExtract(Base):
    '''
    SQLAlchemy ORM class for the tbl_DATA_xeroextract table
    '''

    __tablename__ = r.TBL_DATA_EXTRACT_XERO

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
               " Value: {} >".format(r.TBL_DATA_EXTRACT_XERO,
                                     self.ReportName,
                                     self.DateExtracted,
                                     self.CompanyName,
                                     self.CostCentreName,
                                     self.AccountCode,
                                     self.AccountName,
                                     self.Period,
                                     self.Value)




