# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime

from box.ext import db


# todo 不知道干嘛的 这个类 又没有被用过。。管理员类？
class ExternalUser(db.Model):
    __tablename__ = 'external_user'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    external_uid = db.Column(db.String(256), nullable=False)
    provider = db.Column(db.String(32), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)
