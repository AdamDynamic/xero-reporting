#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Contains custom error classes used in the other modules to handle workflow
'''


class PeriodIsLockedError(AttributeError):
    '''
    Customer error class raised when an action is attempted on a period that is locked in the database
    '''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class PeriodNotFoundError(AttributeError):
    '''
    Customer error class raised when an action is attempted on a preiod that doesn't exist in the database
    '''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class TableEmptyForPeriodError(AttributeError):
    '''
    Customer error class raised when a given table doesn't contain any records for a given period
    '''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class UnallocatedCostsNotNilError(AttributeError):
    '''
    Customer error class raised when a given table doesn't contain any records for a given period
    '''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class MasterDataIncompleteError(AttributeError):
    '''
    Customer error class raised when a given table doesn't contain any records for a given period
    '''
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)