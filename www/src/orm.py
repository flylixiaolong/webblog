#!/usr/bin/env python
#-*- coding:utf-8 -*-

import logging,time
import db

class Field(object):
    _count = 0
    def __init__(self, **kw):
        self.name = kw.get('name',None)
        self._default = kw.get('default',None)
        self.primary_key = kw.get('primary_key',False)
        self.nullable = kw.get('nullable',False)
        self.updatable = kw.get('updatable',True)
        self.insertable = lw.get('insertable',True)
        self.dd1 = kw.get('dd1','')
        self._order = Field._count
        Field._count = Field._count + 1
    @property
    def default(self):
        d = self._default
        return d() if callable(d) else d
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
            rase AttributeError(r"'Dict' object has no attribute %s" % key)
    def __setattr__(self,key,value):
        self[key]=value

    @classmethod
    def get(cls,pk):
        item = db.select_one('select * from %s where %s=?' % （cls.__table__,cls.primary_key__.name), pk)
        return cls(**item) if item else None
    @classmethod
    def find_first(cls,where,*args):
        item = db.select_one('selct * from %s where %s' % (cls.__table__,where),*args)
        return [cls(**item) if item  else None]
    @classmethod
    def find_all(cls,*args):
        items = db.select('select * from %s' % cls.__table__)
        return [cls(**d) for d in items]
    @classmethod
    def find_by(cls,where,*args):
        items = db.select('select * from %s where %s' % (cls.__table__,where),*args)
        return [cls(**d) for d in items]
    @classmethod
    def count_all(cls):
        return db.select_int('select count (%s) from %s' % (cls.__primary_key__.name,cls.__table))
    @classmethod
    def cont_by(cls,where,*args):
        return db.select_int('select count (%s) form %s %s' % (cls.__primary_key.name,cls.__table__,where), *args)
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
        db.update('update %s set %s where %s = ?' % (self.__table__,','.join(items),pk),*args)
        return self
    def insert(self):
        self.pre_insert and self.pre_insert()
        params = {}
        for key,value in self.__mappings__.iteritems():
            if value.insertable:
                if not hasattr(self,key):
                    setattr(self,key,value.default)
                params[value.name] = getattr(self,key)
        db.insert('%s' %self.__table__,**params)
        return self
    def delete(self):
        self.pre_delete and self.pre_delete()
        pd = self.__primary_key__.name
        args = (getattr(self,pk),)
        db.update('delete from %s where %s = ?' % (self.__table__,pk),*args)
        return self
