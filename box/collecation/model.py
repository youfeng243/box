# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime

from box.account.model import User
from box.ext import db
from box.pocket.model import Pocket
from box.utils import logger


def gen_item_id(user_id):
    now = datetime.now()
    return '%s%04d%s%s' % (now.strftime('%y%m%d%H%I'),
                           user_id,
                           now.strftime('%S'),
                           now.strftime("%f")[:2])


# 存储管理表结构
class Collecation(db.Model):
    __tablename__ = 'collecation'

    # 最大剩余天数
    DEFAULT_MAX_REMAIN_DAYS = 2147483647

    # 未被使用
    STATUS_UNUSE = 0

    # todo 不知何意
    # STATUS_REQUESTED = 1

    # 正在被使用 正在进行中？
    STATUS_USING = 2

    # # todo 既然有被使用中 为何还需要被使用过字段?  已经被使用？
    # STATUS_USED = 3

    id = db.Column(db.Integer, primary_key=True)

    # 存储的用户信息
    user_id = db.Column(db.Integer, nullable=False)

    # 存储计费方式
    mode_id = db.Column(db.Integer, nullable=True)

    # 箱子的编码信息，通过时间和用户信息生成
    item_id = db.Column(db.String(32), nullable=False)

    # 当前箱子的使用状态
    status = db.Column(db.Integer, nullable=False, default=STATUS_UNUSE)

    # 存储天数 已经存了多少天了
    days = db.Column(db.Integer, nullable=False, default=0)

    # 剩余天数 通过余额计算出来的 已入库后才开始进行剩余天数计算
    remain_days = db.Column(db.Integer, nullable=False, index=True, default=DEFAULT_MAX_REMAIN_DAYS)

    # 存储订单创建时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 用户开始使用存储的时间 微信端点击入库时间 其实还没入库
    requested_at = db.Column(db.DateTime, default=None)

    # 客服已经把箱子入库的时间 扣费也是根据这个时间算的 入库的时间
    used_at = db.Column(db.DateTime, default=None)

    # 用户添加的备注信息
    remark = db.Column(db.String(512), nullable=True)

    # 未寄回
    STAGE_NOT_SEND_BACK = 1

    # 已寄回
    STAGE_SEND_BACK = 2

    # 已销毁
    STAGE_DESTROY = 3

    # 查询全部状态
    STAGE_ALL = 100

    # 当前阶段
    stage = db.Column(db.Integer, index=True, default=STAGE_NOT_SEND_BACK)

    # 未入库
    STORAGE_NOT_PUT_IN = 0

    # 已入库
    STORAGE_PUT_IN = 1

    # 查询全部状态
    STORAGE_ALL = 100

    # 入库状态
    put_in_status = db.Column(db.Integer, index=True, default=STORAGE_NOT_PUT_IN)

    # 货架号 存储位置
    goods_address = db.Column(db.String(64), default='')

    @classmethod
    def create(cls, user_id, mode_id, item_id):
        obj = cls(user_id=user_id, mode_id=mode_id, item_id=item_id)
        db.session.add(obj)
        db.session.commit()
        return obj

    def save(self):
        """Proxy method of saving object to database"""
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_multi_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()

    # 获得已经入库的箱子
    @classmethod
    def get_used_coll_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id,
                                   put_in_status=cls.STORAGE_PUT_IN).all()

    @classmethod
    def get(cls, id_):
        return cls.query.get(id_)

    # 分页查询
    @classmethod
    def collection_paginate(cls, page, stage, put_in_status, size=10):
        # 已经被使用的订单
        query = cls.query.filter(cls.status == cls.STATUS_USING)

        # 判断是否需要进行分状态查询
        if hasattr(cls, 'stage') and stage != cls.STAGE_ALL:
            query = query.filter(cls.stage == stage)

        # 判断是否需要按入库状态查询
        if hasattr(cls, 'put_in_status') and put_in_status != cls.STORAGE_ALL:
            query = query.filter(cls.put_in_status == put_in_status)

        # 按剩余天数排序
        query = query.order_by('-remain_days')

        return query.paginate(page=page, per_page=size, error_out=False)

    # 获得所有数据量
    @classmethod
    def get_collection_num(cls, stage, put_in_status):
        query = cls.query

        # 判断是否需要进行分状态查询
        if hasattr(cls, 'stage') and stage != cls.STAGE_ALL:
            query = query.filter(cls.stage == stage)

        # 判断是否需要按入库状态查询
        if hasattr(cls, 'put_in_status') and put_in_status != cls.STORAGE_ALL:
            query = query.filter(cls.put_in_status == put_in_status)

        return query.count()

    # 获得所有存储订单信息
    @classmethod
    def get_collection_list(cls, page, stage, put_in_status, size=10):
        result_list = []

        collection_list = cls.collection_paginate(page, stage, put_in_status, size)
        if collection_list is None:
            logger.warn("查询存储订单失败...")
            return result_list
        collection_list = collection_list.items
        if collection_list is None:
            logger.warn("存储订单list获取items字段失败...")
            return result_list

        for item in collection_list:
            result = {
                # 存储ID
                'id': item.id,
                # 箱子编码
                'item_id': item.item_id,
                # 订单时间
                'requested_at': item.requested_at.strftime('%Y-%m-%d %H:%I:%S'),
                # 存储天数
                'days': item.days,
                # 剩余天数
                'remain_days': item.remain_days,
                # 用户姓名
                'nickname': User.get_by_user_id(item.user_id).nickname,
                # 阶段
                'stage': item.stage,
                # 仓库状态
                'put_in_status': item.put_in_status,
                # 货架号
                'goods_address': item.goods_address,

                # 'created_at': item.created_at.strftime('%Y-%m-%d %H:%I:%S'),
                # 'username': item.username,
                # 'mobile': item.mobile,
                # 'address': item.address,
                # 'box_num': item.box_num,
                # 'box_item': box_item,
                # 'status': item.status,
                # 'logistics_no': item.logistics_no,
            }
            # box_item_list = OrderItem.get_multi_by_order_id(item.id)
            # for b_item in box_item_list:
            #     box_item.append(b_item.item_id)

            result_list.append(result)
        return result_list

    # 修改阶段状态
    @classmethod
    def update_stage(cls, c_id, stage):
        if c_id is None or stage is None:
            return False, u'参数错误: c_id = {} stage = {}'.format(c_id, stage)

        collection = cls.query.get(c_id)
        if collection is None:
            return False, u'存储订单不存在!'

        collection.stage = stage
        collection.save()
        return True, u'success'

    # 删除订单
    @classmethod
    def delete(cls, c_id):
        collection = cls.query.get(c_id)
        if collection is None:
            return False, u'存储订单不存在'
        db.session.delete(collection)
        db.session.commit()

        return True, u'success'

    # 入库操作
    @classmethod
    def put_in(cls, c_id, goods_address):
        collection = cls.query.get(c_id)
        if collection is None:
            return False, u'存储订单不存在'

        total_fee = 0

        # 入库地址修改
        collection.goods_address = goods_address
        collection.days = 0

        # 修改状态为入库状态
        collection.put_in_status = cls.STORAGE_PUT_IN

        # 获得开始入库时间
        collection.used_at = datetime.now()

        total_fee += Mode.get_mode_fee(collection.mode_id)

        # 开始计算剩余天数
        # 找出已入库的数据信息
        collection_list = cls.query.filter_by(put_in_status=cls.STORAGE_PUT_IN).all()

        # 获得余额
        balance = Pocket.get_or_create_by_user_id(collection.user_id).balance
        for item in collection_list:
            total_fee += Mode.get_mode_fee(item.mode_id)

        # 获得剩余天数
        collection.remain_days = balance // total_fee
        db.session.add(collection)
        for item in collection_list:
            item.remain_days = balance // total_fee
            db.session.add(collection)

        db.session.commit()
        return True, u'success'

    def as_resp(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'mode_id': self.mode_id,
            'item_id': self.item_id,
            'days': self.days,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%I:%S'),
            'requested_at': (self.requested_at.strftime('%Y-%m-%d')
                             if self.requested_at else None),
            'used_at': (self.used_at.strftime('%Y-%m-%d')
                        if self.used_at else None),
            'remark': self.remark,
        }


# 箱子的存储每天扣费方式
class Mode(db.Model):
    __tablename__ = 'mode'

    # 默认每天扣费情况
    DEFAULT_FEE = 200

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32))
    description = db.Column(db.String(1024))
    price = db.Column(db.Integer)

    @classmethod
    def get(cls, id_):
        return cls.query.get(id_)

    @classmethod
    def get_default_id(cls):
        modes = cls.query.all()
        if modes and len(modes) > 0:
            return modes[0].id

    @classmethod
    def get_mode_fee(cls, mode_id):
        mode = cls.query.get(mode_id)
        if mode is None:
            return cls.DEFAULT_FEE

        return mode.price

    @classmethod
    def get_all(cls):
        return cls.query.all()

    def as_resp(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': self.price
        }
