#!/usr/bin/env python
#-*- coding:utf-8 -*-

import functools

class _Engine(object):
    def __init__(self,connect):
        self.connect = connect
    def connect(self):
        return self._connect()

engine = None

class _LasyConnection(object):
    def __init__(self):
        self.connection = None
    def cursor(self):
        global engine
        if self.connection = None
            connection = engine.connect()
            self.connection = connection()
        return self.connection.cursor()
    def commit(self):
        self.connection.commit()
    def rollback(self):
        self.connection.rollback()
    def cleanup(self):
        if self.connection:
            connection = self.connection
            self.connection = None
            connection.close()
    
class _DbCtx(threading.local):
    def __init__(self):
        self.connection = None
        self.transactions = 0
    def is_init(self):
        return not self.connection is None
    def init(self):
        self.connection = _LasyConnection()
        self.transactions = 0
    def cleanup(self):
        self.connection.cleanup()
        self.connection = None
    def cursor(self):
        return self.connection.cursor()

_db_ctx = _DbCtx()

class _ConnectionCtx(object):
   def __enter__(self):
       global _db_ctx
       self.should_cleanup = False
       if not _db_ctx.is_init():
           _db_ctx.init()
           self.should_cleanup = True
       return self
    def __exit__(self,exctype,excvalue,tracebach):
       global _db_ctx
       if self.should_cleanup:
           _db_ctx.cleanup()

def connection():
    return _ConnectionCtx()

def with_connection(func):
    @functools.wraps(func)    
    def wrapper(*args,**kw):
        print 'call %s:' % func.__name__
        with _ConnectionCtx():
            return fun(*args,**kw)
    return wrapper

class _TransactionCtx(object):
    def __enter__(self):
        global _db_ctx
        self.should_close_conn = False
        if not _db_ctx.init():
            _db_ctx.init()
            self.should_close_conn = True
        _db_ctx.transactions = _db_ctx.transactions + 1
        return self
    def __exit__(self,exctype,excvalue,traceback):
        global _db_ctx
        _db_ctx.transactions = _db_ctx.transactions - 1
        try:
            if _db_ctx.transactions == 0
                if exctype is None:
                self.commit()
            else:
                self.rollback()
        finally:
            if self.should_cleanup:
                _db_ctx.cleanup()
    def commit(self):
        global _db_ctx
        try:
            _db_ctx.connection.commit()
        except:
            _db_ctx.connection.rollback()
            raise
    def rollback(self):
        global _db_ctx
        _db_ctx.connection.rollback()

def transaction():
    return _TransactionCtx()

def with_tarnsaction(func):
    @functolls.wraps(func)
    def wrapper(*args,**kw):
        print 'call %s:' % func.__name__
        with _TransactionCtx():
            return func(*args,*kw)
    return wrapper


