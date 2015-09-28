#!/usr/bin/env python
#-*- coding:utf-8 -*-

import logging
logging.basicConfig(format='%(levelname)s:%(message)s')
import time
import db

class Field(object):
    '''

    >>> testfield=Field(name='lixiaolong',default='test',primary_key=True,ddl='bigint')
    >>> print testfield.default
    test
    >>> print testfield
    <Field:lixiaolong,bigint,default(test),NUI>
    '''
    _count = 0
    def __init__(self, **kw):
        self.name = kw.get('name',None)
        self._default = kw.get('default',None)
        self.primary_key = kw.get('primary_key',False)
        self.nullable = kw.get('nullable',True)
        self.updatable = kw.get('updatable',True)
        self.insertable = kw.get('insertable',True)
        self.ddl = kw.get('ddl','')
        self._order = Field._count
        Field._count = Field._count + 1
    @property
    def default(self):
        return self._default() if callable(self._default) else self._default
    def __str__(self):
        s = ['<%s:%s,%s,default(%s),' % (self.__class__.__name__,self.name,self.ddl,self._default)]
        self.nullable and s.append('N')
        self.updatable and s.append('U')
        self.insertable and s.append('I')
        s.append('>')
        return ''.join(s)

class StringField(Field):
    def __init__(self,**kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'ddl' in kw:
            kw['ddl'] = 'varchar(255)'
        super(StringField,self).__init__(**kw)

class FloatField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = 0.0
        if not 'ddl' in kw:
            kw['ddl'] = 'real'
        super(FloatField, self).__init__(**kw)

class BooleanField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = False
        if not 'ddl' in kw:
            kw['ddl'] = 'bool'
        super(BooleanField, self).__init__(**kw)

class TextField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'ddl' in kw:
            kw['ddl'] = 'text'
        super(TextField, self).__init__(**kw)

class BlobField(Field):
    def __init__(self, **kw):
        if not 'default' in kw:
            kw['default'] = ''
        if not 'ddl' in kw:
            kw['ddl'] = 'blob'
        super(BlobField, self).__init__(**kw)

class VersionField(Field):
    def __init__(self, name=None):
        super(VersionField, self).__init__(name=name, default=0, ddl='bigint')

_triggers = frozenset(['pre_insert', 'pre_update', 'pre_delete'])

class ModelMetaclass(type):
    '''
    This is a Metaclass to create class.When Createing class name is
    Model then return the class not modified, otherwise return the
    modified the class and return it.

    >>> class Model(object):
    ...     __metaclass__ = ModelMetaclass
    ...     def __str__(self):
    ...         return ('%s' % self.__mappings__['id'])
    >>> c1 = Model()
    >>> print c1
    Traceback (most recent call last):
    ...
    AttributeError: 'Model' object has no attribute '__mappings__'
    >>> class User(Model):
    ...     id = StringField(name='name',primary_key=True)
    ...     def __init__(self, arg):
    ...         super(User, self).__init__()
    ...         self.arg = arg
    ...
    >>> c2 = User('lixioalong')
    >>> print c2
    <StringField:name,varchar(255),default(),I>
    '''
    def __new__(cls,name,bases,attrs):
        if name == 'Model':
            return type.__new__(cls,name,bases,attrs)
        #注意cls表示当前类，所以cls.subclasses是当前类的属性
        #即ModelMetaclass的属性，而不是实例属性
        if not hasattr(cls,'subclasses'):
            cls.subclasses = {}
        if not name in cls.subclasses:
            cls.subclasses[name] = name
        else:
            logging.warning('Redefine class: %s' % name)
        logging.info('Scan ORMapping %s...' % name)
        mappings = {}
        primary_key = None
        for key,value in attrs.iteritems():
            if isinstance(value,Field):
                if not value.name:
                    value.name = key
                logging.info('<class:%s>Found mapping: %s ==> %s.' % (name,key,value))
                #拥有主键
                if value.primary_key:
                    #是否已经检测到了主键
                    if primary_key:
                       raise TypeError('Cannot define more than 1 primary key in class %s' % name)
                    if value.updatable:
                       logging.warning('<class:%s> change primary key to non-updatable.' % name)
                       value.updatable = False
                    if value.nullable:
                       logging.warning('<class:%s> change primary key to non-nullable.' % name)
                       value.nullable = False
                    primary_key = value
                mappings[key] = value
        if not primary_key:
            raise TypeError('Primary key not defined in class: %s' % name)
        #从类属性中删除，避免访问时出现冲突
        for key in mappings.iterkeys():
            attrs.pop(key)
        if not '__table__' in attrs:
            attrs['__table__'] = name.lower()
        attrs['__mappings__'] = mappings
        attrs['__primary_key__'] = primary_key
        attrs['__sql__'] = lambda self: _gen_sql(attrs['__table__'],mappings)
        for trigger in _triggers:
            if not trigger in attrs:
                attrs[trigger] = None
        return type.__new__(cls,name,bases,attrs)

class Model(dict):
    __metaclass__ = ModelMetaclass
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute %s" % key)
    def __setattr__(self,key,value):
        self[key]=value
    @classmethod
    def get(cls,pk):
        item = db.select_one('select * from `%s` where %s=?' % (cls.__table__,cls.primary_key__.name), pk)
        return cls(**item) if item else None
    @classmethod
    def find_first(cls,where,*args):
        item = db.select_one('select * from `%s` %s' % (cls.__table__,where),*args)
        return cls(**item) if item else None
    @classmethod
    def find_all(cls,*args):
        items = db.select('select * from `%s`' % cls.__table__)
        return [cls(**d) for d in items]
    @classmethod
    def find_by(cls,where,*args):
        items = db.select('select * from `%s` where %s' % (cls.__table__,where),*args)
        return [cls(**d) for d in items]
    @classmethod
    def count_all(cls):
        return db.select_int('select count (%s) from `%s`' % (cls.__primary_key__.name,cls.__table))
    @classmethod
    def conut_by(cls,where,*args):
        return db.select_int('select count (%s) form `%s` %s' % (cls.__primary_key.name,cls.__table__,where), *args)
    def update(self):
        self.pre_update and self.pre_update()
        items = []
        args = []
        for key,value in self.__mappings__.iteritems():
            if value.updatable:
                if hasattr(self,key):
                    arg = getattr(self,key)
                else:
                    arg = value.default
                    setattr(self,key,value)
                items.append('%s = ?' % key)
                args.append(arg)
        pk = self.__primary_key__.name
        args.append(getattr(self,pk))
        db.update('update `%s` set %s where %s = ?' % (self.__table__,','.join(items),pk),*args)
        return self
    def insert(self):
        self.pre_insert and self.pre_insert()
        params = {}
        for key,value in self.__mappings__.iteritems():
            if value.insertable:
                if not hasattr(self,key):
                    setattr(self,key,value.default)
                params[value.name] = getattr(self,key)
        db.insert('%s' % self.__table__,**params)
        return self
    def delete(self):
        self.pre_delete and self.pre_delete()
        pd = self.__primary_key__.name
        args = (getattr(self,pk),)
        db.update('delete from `%s` where %s = ?' % (self.__table__,pk),*args)
        return self

if __name__=='__main__':
    import doctest
    doctest.testmod()
