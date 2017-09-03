# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime

from box.ext import db


# 产品, 目前只有一种箱子，应该是为看扩展以后会有多种箱子
class Product(db.Model):
    __tablename__ = 'product'

    # 产品的ID信息
    id = db.Column(db.Integer, primary_key=True)
    # 产品名称
    name = db.Column(db.String(128), nullable=False)
    # 产品价格
    price = db.Column(db.Integer)
    # 产品描述
    description = db.Column(db.String(1024), nullable=True)
    avatar_url = db.Column(db.String(1024), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, default=None)

    def save(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get(cls, id_):
        return cls.query.get(id_)

    @classmethod
    def get_all(cls):
        return cls.query.all()

    def as_resp(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'avatar_url': self.avatar_url,
            'price': self.price,
        }


# todo 这个类没有用到
class Intentory(db.Model):
    __tablename__ = 'intentory'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, nullable=False)
    count = db.Column(db.Integer, nullable=False)
