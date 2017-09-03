# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
from datetime import datetime

from box.ext import db


# 生成支付流水账号
def gen_payment_no(user_id):
    now = datetime.now()
    return 'P-%s%04d%s%s' % (now.strftime('%Y%m%d%H%I'),
                             user_id,
                             now.strftime('%S'),
                             now.strftime("%f"))


# 支付信息
class Payment(db.Model):
    __tablename__ = 'payment'

    # 充值
    TYPE_RECHARGE = 0
    # 购买
    TYPE_BUY = 1

    STATUS_PENDING = 0
    STATUS_PAID = 1

    id = db.Column(db.Integer, primary_key=True)
    # 那个用户支付的
    user_id = db.Column(db.Integer, nullable=False)
    # 支付的状态
    status = db.Column(db.Integer, default=STATUS_PENDING)
    # 支付类型  是购买还是充值
    payment_type = db.Column(db.Integer)
    # 支付流水账号
    payment_no = db.Column(db.String(32))
    # 此次支付行动的额度
    amount = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.now)
    paid_at = db.Column(db.DateTime, default=None)

    # 备注信息
    _remark = db.Column('remark', db.Text, default='{}')

    @classmethod
    def create(cls, user_id, amount, payment_type):
        payment_no = gen_payment_no(user_id)
        payment = cls(user_id=user_id, payment_no=payment_no,
                      amount=amount, payment_type=payment_type)

        db.session.add(payment)
        db.session.commit()
        return payment

    @classmethod
    def get_by_payment_no(cls, payment_no):
        return cls.query.filter_by(payment_no=payment_no).first()

    @property
    def remark(self):
        return json.loads(self._remark or '{}')

    @remark.setter
    def remark(self, value):
        self._remark = json.dumps(value)
