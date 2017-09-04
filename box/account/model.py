# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
from datetime import datetime

from box.ext import db

reload(sys)
sys.setdefaultencoding("utf-8")


class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    # 用户名
    username = db.Column(db.String(64), nullable=True)
    # 密码
    password = db.Column(db.String(128), nullable=False)
    # 邮箱
    email = db.Column(db.String(256), nullable=True)
    # 手机
    mobile = db.Column(db.String(16), nullable=False)
    # 昵称
    nickname = db.Column(db.String(32), nullable=False)
    # todo 尚未完全搞清
    openid = db.Column(db.String(512), nullable=True)
    # todo 尚未完全搞清
    avatar_url = db.Column(db.String(512), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    # todo 逻辑删除标识??
    deleted_at = db.Column(db.DateTime, default=None)

    @classmethod
    def get_by_user_id(cls, user_id):
        return cls.query.get(user_id)

    @classmethod
    def get_by_mobile(cls, mobile):
        return cls.query.filter_by(mobile=mobile).first()

    @classmethod
    def get_by_openid(cls, openid):
        return cls.query.filter_by(openid=openid).first()

    @classmethod
    def create(cls, mobile, openid):
        user = User(
            password='',
            mobile=mobile,
            # todo 昵称需要通过微信端获取 参考 http://www.cnblogs.com/txw1958/p/weixin76-user-info.html
            nickname='',
            openid=openid,
            avatar_url='/images/avatar.png',
        )
        db.session.add(user)
        db.session.commit()
        return user

    def as_resp(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'mobile': self.mobile,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
        }


class Address(db.Model):
    __tablename__ = 'address'

    id = db.Column(db.Integer, primary_key=True)
    # 对应的User 表 ID 一个用户会有多个address
    user_id = db.Column(db.Integer, nullable=False)

    # 省份
    province = db.Column(db.String(16))
    # 市
    city = db.Column(db.String(64))
    # 区域
    area = db.Column(db.String(32))
    # 详细地址
    location = db.Column(db.String(128))
    # 联系人名称
    contact_name = db.Column(db.String(32))
    # 联系人电话
    contact_phone = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow)
    # todo 逻辑删除标识???
    deleted_at = db.Column(db.DateTime, default=None)

    # 根据用户ID 获取多个地址信息
    @classmethod
    def get_multi_by_uid(cls, user_id):
        return cls.query.filter_by(user_id=user_id).all()

    # 地址ID 信息
    @classmethod
    def get(cls, address_id):
        return cls.query.get(address_id)

    # 创建地址对象
    @classmethod
    def create(cls, user_id, province, city, area, location,
               contact_name, contact_phone):
        address = Address(
            user_id=user_id,
            province=province,
            city=city,
            area=area,
            location=location,
            contact_name=contact_name,
            contact_phone=contact_phone)
        db.session.add(address)
        db.session.commit()
        return address

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def as_resp(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'province': self.province,
            'city': self.city,
            'area': self.area,
            'location': self.location,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
        }
