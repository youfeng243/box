#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: model.py
@time: 2017/9/2 19:32
"""
from datetime import datetime

from flask_login import UserMixin

from box.ext import db


class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password = db.Column(db.String(64), nullable=False)

    # 生效时间 创建时间
    ctime = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

    # 数据更新时间
    utime = db.Column(db.DateTime(), default=datetime.utcnow, nullable=False)

    # def __init__(self, username, password):
    #     self.username = username
    #     self.password = password

    # 查找用户密码信息
    @classmethod
    def get_admin(cls, username, password):
        return cls.query.filter_by(username=username, password=password).first()

    @classmethod
    def get_admin_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    # 创建地址对象
    @classmethod
    def create(cls, username, password):
        admin = cls(username=username, password=password)
        db.session.add(admin)
        db.session.commit()
        return admin

    def save(self):
        db.session.add(self)
        db.session.commit()

    def as_resp(self):
        return {
            'id': self.id
        }
