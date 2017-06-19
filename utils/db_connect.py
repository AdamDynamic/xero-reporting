#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Connects to the external database used to store output from the program
'''

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base

from references_private import DB_CONNECTION_STRING_MYSQL

# Create database sessionmakers
_engine = create_engine(DB_CONNECTION_STRING_MYSQL)
_base = declarative_base()
_base.metadata.bind = _engine

db_sessionmaker = scoped_session(sessionmaker(bind=_engine, autoflush=False))
