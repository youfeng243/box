# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime

from box.ext import db


# 钱包
class Pocket(db.Model):
    __tablename__ = 'pocket'

    id = db.Column(db.Integer, primary_key=True)
    # 用户信息
    user_id = db.Column(db.Integer, nullable=False)
    # 钱包总额
    balance = db.Column(db.Integer)

    @classmethod
    def create(cls, user_id, balance=0):
        p = cls(user_id=user_id, balance=balance)
        db.session.add(p)
        db.session.commit()
        return p

    @classmethod
    def get_or_create_by_user_id(cls, user_id):
        p = cls.query.filter_by(user_id=user_id).first()
        if p is not None:
            return p

        return cls.create(user_id)

    # 充值
    def add(self, amount, product=None, description=None):
        self.balance += amount
        db.session.add(self)

        if product is None:
            product_id = None
        else:
            product_id = product.id

        # 增加充值记录
        ph = PocketHistory(
            user_id=self.user_id,
            product_id=product_id,
            total_fee=amount,
            balance=self.balance,
            description=description, )
        db.session.add(ph)
        db.session.commit()

    # 消费
    def cut_down(self, amount, product=None, description=None):
        self.balance -= amount
        db.session.add(self)

        if product is None:
            product_id = None
        else:
            product_id = product.id

        # 增加消费记录
        ph = PocketHistory(
            user_id=self.user_id,
            product_id=product_id,
            total_fee=-amount,
            balance=self.balance,
            description=description, )
        db.session.add(ph)
        db.session.commit()

    def as_resp(self):
        history = PocketHistory.get_multi_by_user_id(self.user_id)
        return {
            'user_id': self.id,
            'balance': self.balance,
            'history': [each.as_resp() for each in history]
        }


# 消费记录
class PocketHistory(db.Model):
    __tablename__ = 'pocket_history'

    id = db.Column(db.Integer, primary_key=True)
    # 用户信息
    user_id = db.Column(db.Integer, nullable=False)
    # 产品信息 这里不应该是绑定关系的
    product_id = db.Column(db.Integer, nullable=True)
    # 消费或者充值额度
    total_fee = db.Column(db.Integer, nullable=False)
    # 总钱数目
    balance = db.Column(db.Integer, nullable=False)
    # 描述
    description = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @classmethod
    def get_multi_by_user_id(cls, user_id):
        return (cls.query.filter_by(user_id=user_id)
                .order_by(cls.id.desc()).limit(5).all())

    def as_resp(self):
        return {
            'total_fee': self.total_fee,
            'description': self.description,
            'created_at': self.created_at.strftime('%Y-%m-%d'),
        }
