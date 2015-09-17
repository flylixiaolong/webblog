#!/usr/bin/env python
#-*- coding:utf-8 -*-

import logging,time
import db

class Model(dict):
    __metaclass__ = ModelMetaclass
    def __init__(self,**kw):
        super(Model,self).__init__(**kw)
    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            rase AttributeError(r"'Dict' object has no attribute %s" % key)
    def __setattr__(self,key,value):
        self[key]=value

class ModelMetaclass(type):
    def __new__(cls,name,base,attrs):
        if name == 'Model':
            return type.__new__(cls,name,base,attrs)
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
                logging.info('Found mapping: %s ==> %s' % (key,value)
                #拥有主键
                if value.primary_key:
                    #是否已经检测到了主键
                    if primary_key:
                       raise TypeError('Cannot define more than 1 primary key in class %s' % name)
                    if value.updatable:
                       logging.warning('NOTE: change primary key to non-updatable.')
                       value.updatable = False 
                    if value.nullable:
                       logging.warning('NOTE: change primary key to non-nullable.')
                       value.nullable = False
                    primary_key = value
                mappings[s] = v
        if not primary_key:
            raise TypeErrot('Primary key not defined in class: %s' % name)
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

                    
                    

