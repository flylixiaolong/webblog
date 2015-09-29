#!/usr/bin/env python
#-*- coding:utf-8 -*-

import logging
logging.basicConfig(level='INFO')
import threading
from datetime import datetime, timedelta, tzinfo
import re

ctx = threading.local()

class Dict(dict):
    '''
    Simple dict but support access as x.y style.
    >>> d1 = Dict()
    >>> d1['x'] = 100
    >>> d1.x
    100
    >>> d1.y = 200
    >>> d1['y']
    200
    >>> d2 = Dict(a=1, b=2, c='3')
    >>> d2.c
    '3'
    >>> d2['empty']
    Traceback (most recent call last):
        ...
    KeyError: 'empty'
    >>> d2.empty
    Traceback (most recent call last):
        ...
    AttributeError: 'Dict' object has no attribute 'empty'
    >>> d3 = Dict(('a', 'b', 'c'), (1, 2, 3))
    >>> d3.a
    1
    >>> d3.b
    2
    >>> d3.c
    3
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for key, value in zip(names, values):
            self[key] = value
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)
    def __setattr__(self, key, value):
        self[key] = value

_RE_TZ = re.compile('^([\+|\-])(\d{1,2})\:(\d{1,2})$')
class UTC(tzinfo):
    '''
    This is the tzinfo subclass to transition times to local time zone.

    >>> utc1 = UTC('+08:00')
    >>> utc1.tzname()
    >>> utc1.dst(None)
    >>> utc1.utcoffset(None)
    >>> utc0 = UTC('+00:00')
    >>> utc0.tzname()

    '''
    def __init__(self, utc='+00:00'):
        utc = utc.strip().upper()
        mt   = _RE_TZ.match(utc)
        if mt:
            minus = mt.group(1)=='-'
            h = int(mt.group(2))
            m = int(mt.group(3))
            if minus:
                h, m = (-h), (-m)
            self._utcoffset = timedelta(hours=h, minutes=m)
            self._tzname = 'UTC%s' % utc
        else:
            raise ValueError('bad utc time zone: %s' % utc)
    def utcoffset(self, dt):
        return self._utcoffset+self.dst(dt)
    def dst(self,dt):
        # Code to set dston and dstoff to the time zone's DST
        # transition times based on the input dt.year, and expressed
        # in standard local time.  Then
        # if dston <= dt.replace(tzinfo=None) < dstoff:
        #     return timedelta(hours=1)
        # else:
        #     return timedelta(0)
        return timedelta(0)
    def tzname(self):
        return self._tzname
    def __str__(self):
        return "UTC tzinfo object (%s)" % self._tzname
    __repr__=__str__
        
        
class HttpError(Exception):
    pass

class Request(object):
    def get(self,key,default=None):
        pass
    def input(self):
        pass
    @property
    def path_info(self):
        pass
    @property
    def headers(self):
        pass
    def cookie(self,name,default=None):
            pass    
    def set_cookie(self,name,value,max_age=None,expire=None,path='/'):
        pass
    @property
    def status(self):
        pass
    @status.setter
    def status(self,value):
        pass

def get(path):
    pass    
def pose(path):
    pass
def view(path):
    pass
def interceptor(pattern):
    pass

class TemplateEngine(object):
    def __call__(self,path,model):
        pass

class Jinja2TemplateEngine(TemplateEngine):
    def __init(self,template_dir,**kw):
        from jinjia2 import Environment, FileSystemLoader
        self._env = Environment(loader=FileSystemLoader(template_dir),**kw)
    def __call__(self,path,model):
        return self._env.get_template(path).render(**model).encode('utf-8')

class WSGIApplication(object):
    def __init__(self,document_root=None,**kw):
        pass
    def add_url(self,func):
        pass
    def add_interceptor(self,func):
        pass
    @property
    def template_engine(self):
        pass
    @template_engine.setter
    def template_engine(self,engine):
        pass
    def get_wsgi_application(self):
        def wsgi(env,star_response):
            pass
        return wsgi
    def run(self,port=9000,host='127.0.0.1'):
        from wsgiref.simple_server import make_server
        server = make_server(host,port,self.get_wsgi_application())
        server.serve_forever()
        
wsgi = WSGIApplication()
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    wsgi.run()
else:
    application = wsgi.get_wsgi_application()       
