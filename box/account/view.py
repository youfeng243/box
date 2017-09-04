# -*- coding: utf-8 -*-
import json
import sys

from flask import Blueprint, request, session

from box.account.model import User, Address
from box.captcha.sms import validate_captcha
from box.const import (HTTP_BAD_REQUEST, HTTP_UNAUTHORIZED, HTTP_NOT_FOUND,
                       EMSG_PARAMS_MISSING, HTTP_OK)
from box.utils import logger
from box.utils.api import success, fail
from box.wechat.auth import wechat_login, get_current_user

reload(sys)
sys.setdefaultencoding("utf-8")

bp = Blueprint('account', __name__)
bp.before_request(wechat_login)

c_bp = Blueprint('current', __name__)


# 根据openid获得当前用户信息
@c_bp.route('/api/current', methods=['GET'])
def current():
    openid = session.get('openid', None)
    if openid is None:
        return fail(HTTP_UNAUTHORIZED)

    user = User.get_by_openid(openid)
    if user is None:
        return fail(HTTP_UNAUTHORIZED)

    return success(user.as_resp())


# 用户注册，需要通过微信端进行注册
@bp.route('/api/account/profile', methods=['POST'])
def create_profile():
    openid = session.get('openid', None)
    if openid is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端访问')

    user = User.get_by_openid(openid)
    if user is not None:
        return fail(HTTP_BAD_REQUEST, u'用户已注册')

    if request.json is None:
        return fail(HTTP_BAD_REQUEST)

    mobile = request.json.get('mobile', None)
    if mobile is None:
        return fail(HTTP_BAD_REQUEST, u'请输入手机号')

    code = request.json.get('code', None)
    if code is None:
        return fail(HTTP_BAD_REQUEST, u'请输入验证码')

    # 校验手机验证码
    if validate_captcha(mobile, code):
        user = User.create(mobile, openid)
        return success(user.as_resp())

    return fail(HTTP_BAD_REQUEST, u'验证码错误')


# 获取当前用户所有的地址信息
@bp.route('/api/current/address', methods=['GET'])
def address_list():
    current_user = get_current_user()
    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')

    rv = [each.as_resp() for each in Address.get_multi_by_uid(current_user.id)]
    return success(rv)


# 创建新的用户地址
@bp.route('/api/current/address', methods=['POST'])
def create_address():
    current_user = get_current_user()
    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')

    user_id = current_user.id
    if request.json is None:
        return fail(HTTP_BAD_REQUEST, EMSG_PARAMS_MISSING)

    logger.info(json.dumps(request.json, ensure_ascii=False))

    province = request.json.get('province')
    logger.info("province = {}".format(province))

    city = request.json.get('city')
    area = request.json.get('area')
    location = request.json.get('location')
    contact_name = request.json.get('contact_name')
    contact_phone = request.json.get('contact_phone')

    addr = Address.create(
        user_id=user_id,
        province=province,
        city=city,
        area=area,
        location=location,
        contact_name=contact_name,
        contact_phone=contact_phone,
    )

    return success(addr.as_resp())


# 修改地址信息
@bp.route('/api/current/address/<int:a_id>', methods=['POST', 'GET'])
def update_address(a_id):
    current_user = get_current_user()
    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')

    addr = Address.get(a_id)
    if addr is None or addr.user_id != current_user.id:
        return fail(HTTP_NOT_FOUND, u'地址不存在')

    if request.method == 'POST':
        province = request.json.get('province')
        city = request.json.get('city')
        area = request.json.get('area')
        location = request.json.get('location')
        contact_name = request.json.get('contact_name')
        contact_phone = request.json.get('contact_phone')

        addr.province = province
        addr.city = city
        addr.area = area
        addr.location = location
        addr.contact_name = contact_name
        addr.contact_phone = contact_phone

        addr.save()
        return success(addr.as_resp())
    elif request.method == 'GET':
        return success(addr.as_resp())

    return fail(HTTP_OK, u'未知异常..')


# 删除地址信息
@bp.route('/api/current/address/<int:id>', methods=['DELETE'])
def delete_address(id):
    current_user = get_current_user()
    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')

    addr = Address.get(id)
    if addr is None:
        return fail(HTTP_NOT_FOUND, u'地址未找到')

    addr.delete()

    return success(None)
