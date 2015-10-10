#!/usr/bin/env python
# -*- coding:utf-8 -*-

from src.web import get,view
from src.model import User, Blog, Comment

@view('test_users.html')
@get('/')
def test_users():
    users = User.find_all()
    return dict(users=users)