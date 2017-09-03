#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: login_manager.py
@time: 2017/9/2 20:14
"""
from flask_login import LoginManager

from box.admin.model import Admin

login_manager = LoginManager()


@login_manager.user_loader
def user_loader(admin_id):
    return Admin.query.get(admin_id)


def setup_login_manager(app):
    login_manager.init_app(app)
