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
    'UTC+08:00'
    >>> utc1.dst(None)
    datetime.timedelta(0)
    >>> utc1.utcoffset(None)
    datetime.timedelta(0, 28800)
    >>> utc2 = UTC('+10:00')
    >>> utc2.tzname()
    'UTC+10:00'
    >>> dt1 = datetime(2006, 11, 21, 16, 30, tzinfo=utc1)
    >>> dt1.utcoffset()
    datetime.timedelta(0, 28800)
    >>> dt1.dst()
    datetime.timedelta(0)
    >>> dt2=dt1.astimezone(utc2)
    >>> dt2.dst()
    datetime.timedelta(0)
    >>> dt2.utcoffset()
    datetime.timedelta(0, 36000)
    >>> dt1
    datetime.datetime(2006, 11, 21, 16, 30, tzinfo=UTC tzinfo object (UTC+08:00))
    >>> dt2
    datetime.datetime(2006, 11, 21, 18, 30, tzinfo=UTC tzinfo object (UTC+10:00))
    >>> dt1==dt2
    True
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
    def utcoffset(self, dt=None):
        return self._utcoffset+self.dst(dt=None)
    def dst(self,dt=None):
        # Code to set dston and dstoff to the time zone's DST
        # transition times based on the input dt.year, and expressed
        # in standard local time.  Then
        # if dston <= dt.replace(tzinfo=None) < dstoff:
        #     return timedelta(hours=1)
        # else:
        #     return timedelta(0)
        return timedelta(0)
    def tzname(self,dt=None):
        return self._tzname
    def __str__(self):
        return "UTC tzinfo object (%s)" % self._tzname
    __repr__=__str__
        
# all known response statues:
_RESPONSE_STATUSES = {
    # Informational
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',

    # Successful
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi Status',
    226: 'IM Used',

    # Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',

    # Client Error
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a teapot",
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',

    # Server Error
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    507: 'Insufficient Storage',
    510: 'Not Extended',
}

_RE_RESPONSE_STATUS = re.compile(r'^\d\d\d(\ [\w\ ]+)?$')

_RESPONSE_HEADERS = (
    'Accept-Ranges',
    'Age',
    'Allow',
    'Cache-Control',
    'Connection',
    'Content-Encoding',
    'Content-Language',
    'Content-Length',
    'Content-Location',
    'Content-MD5',
    'Content-Disposition',
    'Content-Range',
    'Content-Type',
    'Date',
    'ETag',
    'Expires',
    'Last-Modified',
    'Link',
    'Location',
    'P3P',
    'Pragma',
    'Proxy-Authenticate',
    'Refresh',
    'Retry-After',
    'Server',
    'Set-Cookie',
    'Strict-Transport-Security',
    'Trailer',
    'Transfer-Encoding',
    'Vary',
    'Via',
    'Warning',
    'WWW-Authenticate',
    'X-Frame-Options',
    'X-XSS-Protection',
    'X-Content-Type-Options',
    'X-Forwarded-Proto',
    'X-Powered-By',
    'X-UA-Compatible',
)

_RESPONSE_HEADER_DICT = dict(zip(map(lambda x: x.upper(), _RESPONSE_HEADERS), _RESPONSE_HEADERS))

_HEADER_X_POWERED_BY = ('X-Powered-By', 'src/1.0')

class HttpError(Exception):
    '''
    HttpError that defines http error code

    >>> e = HttpError(404)
    >>> e.status
    '404 Not Found'
    '''
    def __init__(self,code):
        '''
        Init an HttpError with response code
        '''
        super(HttpError,self).__init__()
        self.status = '%d %s' % (code, _RESPONSE_STATUSES[code])
    def header(self,name,value):
        if not hasattr(self,'_headers'):
            self._headers = [_HEADER_X_POWERED_BY]
        self._headers.append((name,value))
    @property
    def headers(self):
        if hasattr(self,'_headers'):
            return self._headers
        return []
    def __str__(self):
        return self.status
    __repr__ = __str__
    
class RedirectError(HttpError):
    '''
    RedirectError that defines http redirect code.

    >>> e = RedirectError(302,'http://www.apple.com/')
    >>> e.status
    '302 Found'
    >>> e.Location
    'http://www.apple.com/'
    '''
    def __init__(self, code, location):
        '''
        Init an HttpError with response code.
        '''
        super(RedirectError, self).__init__(code)
        self.location = location
    def __str__(self):
        return '%s, %s' % (self.status, self.location)
    __repr__ = __str__

def badrequest():
    '''
    Send a bad request response.
    >>> raise badrequest()
    Traceback (most recent call last):
      ...
    HttpError: 400 Bad Request
    '''
    return HttpError(400)

def forbidden():
    '''
    Send a forbidden response.
    >>> raise forbidden()
    Traceback (most recent call last):
      ...
    HttpError: 403 Forbidden
    '''
    return HttpError(403)

def notfound():
    '''
    Send a not found response.
    >>> raise notfound()
    Traceback (most recent call last):
      ...
    HttpError: 404 Not Found
    '''
    return HttpError(404)

def conflict():
    '''
    Send a conflict response.
    >>> raise conflict()
    Traceback (most recent call last):
      ...
    HttpError: 409 Conflict
    '''
    return HttpError(409)

def internalerror():
    '''
    Send an internal error response.
    >>> raise internalerror()
    Traceback (most recent call last):
      ...
    HttpError: 500 Internal Server Error
    '''
    return HttpError(500)

def redirect(location):
    '''
    Do permanent redirect.
    >>> raise redirect('http://www.itranswarp.com/')
    Traceback (most recent call last):
      ...
    RedirectError: 301 Moved Permanently, http://www.itranswarp.com/
    '''
    return RedirectError(301, location)

def found(location):
    '''
    Do temporary redirect.
    >>> raise found('http://www.itranswarp.com/')
    Traceback (most recent call last):
      ...
    RedirectError: 302 Found, http://www.itranswarp.com/
    '''
    return RedirectError(302, location)

def seeother(location):
    '''
    Do temporary redirect.
    >>> raise seeother('http://www.itranswarp.com/')
    Traceback (most recent call last):
     ...
    RedirectError: 303 See Other, http://www.itranswarp.com/
    >>> e = seeother('http://www.itranswarp.com/seeother?r=123')
    >>> e.location
    'http://www.itranswarp.com/seeother?r=123'
    '''
    return RedirectError(303, location)

def _to_str(s):
    '''
    Convert to str.
    >>> _to_str('s123') == 's123'
    True
    >>> _to_str(u'\u4e2d\u6587') == '\xe4\xb8\xad\xe6\x96\x87'
    True
    >>> _to_str(-123) == '-123'
    True
    '''
    if isinstance(s, str):
        return s
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return str(s)

def _to_unicode(s, encoding='utf-8'):
    '''
    Convert to unicode.
    >>> _to_unicode('\xe4\xb8\xad\xe6\x96\x87') == u'\u4e2d\u6587'
    True
    '''
    return s.decode('utf-8')

def _quote(s, encoding='utf-8'):
    '''
    Url quote as str.
    >>> _quote('http://example/test?a=1+')
    'http%3A//example/test%3Fa%3D1%2B'
    >>> _quote(u'hello world!')
    'hello%20world%21'
    '''
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return urllib.quote(s)

def _unquote(s, encoding='utf-8'):
    '''
    Url unquote as unicode.
    >>> _unquote('http%3A//example/test%3Fa%3D1+')
    u'http://example/test?a=1+'
    '''
    return urllib.unquote(s).decode(encoding)

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
    '''
    A @get decorator.
    @get('/:id')
    def index(id):
        pass
    >>> @get('/test/:id')
    ... def test():
    ...     return 'ok'
    ...
    >>> test.__web_route__
    '/test/:id'
    >>> test.__web_method__
    'GET'
    >>> test()
    'ok'
    '''
    def _decorator(func):
        func.__web_route__ = path
        func.__web_method__ = 'GET'
        return func
 
def post(path):
    '''
    A @post decorator.
    >>> @post('/post/:id')
    ... def testpost():
    ...     return '200'
    ...
    >>> testpost.__web_route__
    '/post/:id'
    >>> testpost.__web_method__
    'POST'
    >>> testpost()
    '200'
    '''
    def _decorator(func):
        func.__web_route__ = path
        func.__web_method__ = 'POST'
        return func
    return _decorator
    
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
