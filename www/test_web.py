#!/usr/bin/env python
# -*- coding:utf-8 -*-

from src.web import get,view
from src.model import User, Blog, Comment

@view('__base__.html')
@get('/')
def test_users():
    users = User.find_all()
    return dict(users=users)