#!/usr/bin/env python
#-*- coding:utf-8 -*-

import time,uuid,threading,logging
import functools

class Dict(dict):
    '''
    Simple dict but also support attribute access like d.x

    >>> d=Dict()
    >>> d['a'] = 1
    >>> d['a']
    1
    >>> d.b = 2
    >>> d.b
    2
    >>> d
    {'a': 1, 'b': 2}
    >>> d['c']
    Traceback (most recent call last):
    ...
    KeyError: 'c'
    >>> d.c
    Traceback (most recent call last):
    ...
    AttributeError: 'Dict' object has no attribute c
    >>> d1=Dict(names=['lihong','wangjun'],values=[99,100])
    >>> d1
    {'lihong': 99, 'wangjun': 100}
    '''
    def __init__(self,names=(),values=(),**kw):
        super(Dict,self).__init__(**kw)
        for key,value in zip(names,values):
            self[key] = value
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute %s" % key)
    def __setattr__(self,key,value):
        self[key] = value

def next_id(t=None):
    '''
    To generate the UUID (Universally Unique Identifier)
     '''
    if t is None:
        t = time.time()
    return '%015d%s000' % (int(t * 1000), uuid.uuid4().hex)

def _profiling(start,sql=''):
    t = time.time() - start
    if t > 0.1:
        logging.warning('[PROFILING] [DB] %s: %s' % (t,sql))
    else:
        logging.info('[PROFILING] [DB] %s: %s' % (t,sql))

class DBError(Exception):
    pass

class MultiColumnsError(DBError):
    pass

engine = None

class _Engine(object):
    def __init__(self,connect):
        self._connect = connect
    def connect(self):
        return self._connect()

def create_engine(user,password,database,host='127.0.0.1',port=3306,**kw):
    '''
    Create the Mysql connector Engine

    >>> create_engine('root','123456','myblog')
    >>> create_engine('root','123456','myblog')
    Traceback (most recent call last):
    ...
    DBError: Engine is already initialized.
    '''
    import mysql.connector
    global engine
    engine = None
    if engine is not None:
        raise DBError ('Engine is already initialized.')
    params = dict(user=user,password=password,database=database,host=host,port=port)
    defaults = dict(use_unicode=True,charset='utf8',collation='utf8_general_ci',autocommit=False)
    for key,value in defaults.iteritems():
        params[key] = kw.pop(key,value)
    params.update(kw)
    params['buffered'] = True
    engine = _Engine(lambda: mysql.connector.connect(**params))
    logging.info('Init mysql engine <%s> ok.' % hex (id(engine)))

class _LasyConnection(object):

    def __init__(self):
        self.connection = None
    def cursor(self):
        global engine
        if self.connection == None:
            connection = engine.connect()
            logging.info('open connection <%s>...' % hex(id(connection)))
            self.connection = connection
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
            logging.info('close connection <%s> ok.' % hex (id(connection)))

class _DbCtx(threading.local):
    def __init__(self):
        self.connection = None
        self.transactions = 0
    def is_init(self):
        '''
        return True or False
        when self.connection is None return False
        when self.connection is not None return True
        '''
        return not self.connection is None
    def init(self):
        self.connection = _LasyConnection()
        self.transactions = 0
    def cleanup(self):
        self.connection.cleanup()
        self.connection = None
    def cursor(self):
        return self.connection.cursor()

#_db_ctx is an instance of threading.local,
 #so each threading has his own data.
_db_ctx = _DbCtx()

class _ConnectionCtx(object):
    '''
    _ConnectionCtx has __enter__ and __exit__ method
    it chould use in with sentence, open and close the
    connection automatically.  _ConnectionCtx object 
    can be nested and only the outermost connection 
    has effect.

    Inner _ConnectionCtx object and outermost 
    _ConnectionCtx object have their own should_cleanup
    attribute.

    with _ConnectionCtx():
        pass
    '''
    def __enter__(self):
        global _db_ctx
        self.should_cleanup = False
        #if not init then init
        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_cleanup = True
        return self
    def __exit__(self,exctype,excvalue,tracebach):
       global _db_ctx
       if self.should_cleanup:
           _db_ctx.cleanup()

def connection():
    '''
    Return _ConnectionCtx object that can be 
    used by 'with' statement like:
    with connection():
        pass
    '''
    return _ConnectionCtx()

def with_connection(func):
    '''
    This is a Decorator for resuse connection
    
    @with_connection
    def foo(*args, **kw):
        pass
    '''
    @functools.wraps(func)
    def wrapper(*args,**kw):
        logging.info('call function %s:' % func.__name__)
        with _ConnectionCtx():
            return func(*args,**kw)
    return wrapper

class _TransactionCtx(object):
    '''
    _TransactionCtx object that can handle transactions.

    with _TransactionCtx():
        pass
    '''
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
            if _db_ctx.transactions == 0:
                if exctype is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            if self.should_close_conn:
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
    '''
    Create a transaction object so can use with statement:

    with transaction():
        pass

    >>> def update_profile(id, name ,rollback):
    ...    u = dict(id=id,name=name,email='%s@test.org' % name,password=name,created_at=0)
    ...    insert('users',**u)
    ...    r = update('update users set password=? where id=?',name.upper(),id)
    ...    if rollback:
    ...        raise StandardError('will cause roolback...')
    >>> with transaction():
    ...    update_profile(900301,'Python',False)
    insert into `users` (`email`,`created_at`,`password`,`id`,`name`) values (%s,%s,%s,%s,%s) ('Python@test.org', 0, 'Python', 900301, 'Python')
    update users set password=%s where id=%s ('PYTHON', 900301)
    >>> select_one('select * from users where id=?',[900301]).name
    u'Python'
    >>> with transaction():
    ...    update_profile(900302, 'Ruby', True)
    Traceback (most recent call last):
    ...
    StandardError: will cause roolback...
    >>> select('select * from users where id=?', [900302])
    []
    '''
    return _TransactionCtx()

def with_tarnsaction(func):
    '''
    This is a Decorator for resuse connection
    
    @with_tarnsaction
    def foo(*args, **kw):
        pass

    >>> @with_tarnsaction
    ... def update_profile(id, name ,rollback):
    ...     u = dict(id=id,name=name,email='%s@test.org' % name,password=name,created_at=0)
    ...     insert('users',**u)
    ...     r = update('update users set password=? where id=?',name.upper(),id)
    ...     if rollback:
    ...         raise StandardError('will cause roolback...')
    >>> update_profile(900303,'Php',False)
    insert into `users` (`email`,`created_at`,`password`,`id`,`name`) values (%s,%s,%s,%s,%s) ('Php@test.org', 0, 'Php', 900303, 'Php')
    update users set password=%s where id=%s ('PHP', 900303)
    >>> select_one('select * from users where id=?',[900303]).name
    u'Php'
    >>> update_profile(900304, 'Go', True)
    Traceback (most recent call last):
    ...
    StandardError: will cause roolback...
    >>> select('select * from users where id=?', [900304])
    []
    '''
    @functools.wraps(func)
    def wrapper(*args,**kw):
        logging.info('call function %s:' % func.__name__)
        with _TransactionCtx():
            return func(*args,**kw)
    return wrapper

def _select(sql, first, *args):
    ' execute select SQL and return unique result or list results.'
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql, *args)
        if cursor.description:
            names = [x[0] for x in cursor.description]
        if first:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(names, values)
        return [Dict(names, x) for x in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()

@with_connection
def select_one(sql, *args):
    '''
    Return one item metting the conditions.
    
    >>> u1 = dict(id='900305', name='Java', email='Java@test.org', password='Java', created_at='0')
    >>> insert('users',**u1)
    insert into `users` (`email`,`created_at`,`password`,`id`,`name`) values (%s,%s,%s,%s,%s) ('Java@test.org', '0', 'Java', '900305', 'Java')
    1
    >>> select_one('select * from users where id=?', [900305]).name
    u'Java'
    '''
    return _select(sql, True, *args)

@with_connection
def select_int(sql, *args):
    '''
    Return the count metting the conditions.

    >>> select_int('select count(*) from users')
    3
    '''
    d = _select(sql, True, *args)
    if len(d)!=1:
        raise MultiColumnsError('Expect only one column.')
    return d.values()[0]

@with_connection
def select(sql, *args):
    '''
    Return the list metting the conditions.

    >>> u1 = dict(id='900306', name='C#', email='C#@test.org', password='C#', created_at='0')
    >>> insert('users',**u1)
    insert into `users` (`email`,`created_at`,`password`,`id`,`name`) values (%s,%s,%s,%s,%s) ('C#@test.org', '0', 'C#', '900306', 'C#')
    1
    >>> u2 = dict(id='900307', name='Matlab', email='Matlab@test.org', password='Matlab', created_at='0')
    >>> insert('users',**u2)
    insert into `users` (`email`,`created_at`,`password`,`id`,`name`) values (%s,%s,%s,%s,%s) ('Matlab@test.org', '0', 'Matlab', '900307', 'Matlab')
    1
    >>> select('select * from users',[])
    [{u'created_at': 0.0, u'name': u'C#', u'admin': 0, u'image': u'', u'email': u'C#@test.org', u'password': u'C#', u'id': u'900306'}, {u'created_at': 0.0, u'name': u'Matlab', u'admin': 0, u'image': u'', u'email': u'Matlab@test.org', u'password': u'Matlab', u'id': u'900307'}, {u'created_at': 0.0, u'name': u'Perf', u'admin': 0, u'image': u'', u'email': u'Perf@test.org', u'password': u'Perf', u'id': u'900308'}]
    '''
    return _select(sql, False, *args)

@with_connection
def _update(sql, *args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    logging.info('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        print sql,args
        cursor.execute(sql, args)
        r = cursor.rowcount
        if _db_ctx.transactions==0:
            # no transaction enviroment:
            logging.info('auto commit')
            _db_ctx.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()

def insert(table, **kw):
    '''
    Insert values in table.

    >>> u1 = dict(id='900308', name='Perf', email='Perf@test.org', password='Perf', created_at='0')
    >>> insert('users',**u1)
    insert into `users` (`email`,`created_at`,`password`,`id`,`name`) values (%s,%s,%s,%s,%s) ('Perf@test.org', '0', 'Perf', '900308', 'Perf')
    1
    '''
    cols, args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)

def update(sql, *args):
    return _update(sql, *args)

if __name__ == '__main__':
    import doctest
    doctest.testmod()
