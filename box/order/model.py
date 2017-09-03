# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime

from box.account.model import Address
from box.ext import db
from box.product.model import Product


# 一次购买记录信息
class Order(db.Model):
    __tablename__ = 'order'

    # 钱包支付方式
    PAYED_CRASH = 'crash'

    # 微信支付方式
    PAYED_WECHAT = 'wechat'

    # todo 未付款状态?
    STATUS_PENDING = 0

    # # 账户付款 已付款状态
    # STATUS_PAID_BY_CRASH = 1
    # # 微信付款 已付款状态
    # STATUS_PAID_BY_WECHAT = 2

    # 已付款状态
    STATUS_PAYED = 1

    # 已发货状态
    STATUS_SHIPMENTS = 2

    # 取消订单
    STATUS_CANCEL = 3
    # 订单过期
    STATUS_EXPIRED = 4

    # 查询所有
    STATUS_ALL = 100

    id = db.Column(db.Integer, primary_key=True)

    # 哪个用户的订单
    user_id = db.Column(db.Integer, nullable=False)

    # # 箱子订单的初始化地址信息ID
    address_id = db.Column(db.Integer, nullable=False)

    # 用户姓名
    username = db.Column(db.String(32), nullable=False)

    # 手机
    mobile = db.Column(db.String(16), nullable=False)

    # 邮寄地址 初始化时通过 用户传过来的地址id进行填充
    address = db.Column(db.String(128), nullable=False)

    # 付款记录ID
    payment_id = db.Column(db.Integer, nullable=True)

    # 箱子的数目
    box_num = db.Column(db.Integer, nullable=False)

    # 纸箱费用 不懂就看微信公众号怎么下单的 看付费细节
    product_fee = db.Column(db.Integer, nullable=False)
    # 邮寄费用 好像还没用，下单的时候邮寄费用默认为0
    express_fee = db.Column(db.Integer, nullable=False)

    # 物流编号
    logistics_no = db.Column(db.String(128), default='')

    # todo 这个字段没有被使用过，不明白含义
    expire_at = db.Column(db.DateTime, default=None)

    # 订单当前的付款状态
    status = db.Column(db.Integer, index=True, default=STATUS_PENDING)

    # 付款方式
    payment_method = db.Column(db.String(32), default='')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    @classmethod
    def create(cls, user_id, address_id, product_fee, express_fee, box_num=1):
        obj = cls(user_id=user_id, address_id=address_id,
                  product_fee=product_fee, express_fee=express_fee, box_num=box_num)

        # 这里查询地址信息进行初始化
        address = Address.get(address_id)
        obj.address = address.province + address.city + address.area + address.location

        obj.save()
        return obj

    def save(self):
        """Proxy method of saving object to database"""
        db.session.add(self)
        db.session.commit()

    @classmethod
    def delete(cls, order_id):
        order = cls.query.get(order_id)
        if order is None:
            return False, u'订单不存在'
        db.session.delete(order)
        db.session.commit()

        return True, u'success'

    # 通过付款记录获得订单信息
    @classmethod
    def get_by_payment_id(cls, payment_id):
        return cls.query.filter_by(payment_id=payment_id).first()

    # 获得每个箱子的信息
    def get_items(self):
        return OrderItem.get_multi_by_order_id(self.id)

    # 根据不同的状态进行分页查询
    @classmethod
    def order_paginate(cls, page, status, size=10):
        query = cls.query

        # 判断是否需要进行分状态查询
        if hasattr(cls, 'status') and status != cls.STATUS_ALL:
            query = query.filter(cls.status == status)

        return query.paginate(page=page, per_page=size, error_out=False)

    # 获得列表信息
    @classmethod
    def get_order_list(cls, page, status, size=10):
        result_list = []

        item_list = cls.order_paginate(page, status, size=size).items
        if item_list is None:
            return result_list

        for item in item_list:
            box_item = list()
            result = {
                'id': item.id,
                'created_at': item.created_at.strftime('%Y-%m-%d %H:%I:%S'),
                'username': item.username,
                'mobile': item.mobile,
                'address': item.address,
                'box_num': item.box_num,
                'box_item': box_item,
                'status': item.status,
                'logistics_no': item.logistics_no,
            }
            box_item_list = OrderItem.get_multi_by_order_id(item.id)
            for b_item in box_item_list:
                box_item.append(b_item.item_id)

            result_list.append(result)
        return result_list

    # 查询订单数目
    @classmethod
    def get_order_num(cls, status):
        # 查询全部
        if status == cls.STATUS_ALL:
            return cls.query.count()

        return cls.query.filter_by(status=status).count()

    # 修改物流
    @classmethod
    def update_logistics(cls, order_id, logistics_no):

        if order_id is None or logistics_no is None:
            return False, u'参数错误: order_id = {} logistics_no = {}'.format(order_id, logistics_no)

        order = cls.query.get(order_id)
        if order is None:
            return False, u'订单不存在!'

        # 判断订单状态是否正确
        if order.status not in (cls.STATUS_PAYED, cls.STATUS_SHIPMENTS):
            return False, u'订单状态错误，无法修改物流信息: status = {}'.format(order.status)

        order.logistics_no = logistics_no
        order.save()
        return True, u'success'

    # 编辑订单
    @classmethod
    def update_user_info(cls, order_id, username, mobile, address):
        if order_id is None:
            return False, u'订单号错误: order_id = {}'.format(order_id)

        order = cls.query.get(order_id)
        if order is None:
            return False, u'订单不存在!'

        if username is not None:
            order.username = username
        if mobile is not None:
            order.mobile = mobile
        if address is not None:
            order.address = address

        order.save()
        return True, u'success'

    def as_resp(self):
        items = self.get_items()
        return {
            'id': self.id,
            'express_fee': self.express_fee,
            'product_fee': self.product_fee,
            'items': [each.as_resp() for each in items]
        }


# 一次购买记录中不同箱子的信息
class OrderItem(db.Model):
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)

    # 箱子的编号！！！ 根据时间和用户信息生成的
    item_id = db.Column(db.String(128), nullable=True)

    # 购买的用户
    user_id = db.Column(db.Integer, nullable=False)
    # 属于哪一种产品
    product_id = db.Column(db.Integer, nullable=False)
    # 属于哪一个订单的
    order_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    @classmethod
    def create(cls, user_id, product_id, order_id):
        obj = cls(user_id=user_id, product_id=product_id, order_id=order_id)
        db.session.add(obj)
        db.session.commit()
        return obj

    @classmethod
    def get_multi_by_order_id(cls, order_id):
        return cls.query.filter_by(order_id=order_id).all()

    def as_resp(self):
        product = Product.get(self.product_id)
        return {
            'id': self.id,
            'item_id': self.item_id,
            'product': product.as_resp(),
        }
