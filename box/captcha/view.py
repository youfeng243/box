# -*- coding: utf-8 -*-

from envcfg.raw import box as config
from flask import Blueprint, request

from box.account.model import User
from box.captcha.sms import request_sms, mobile_reach_ratelimit
from box.const import HTTP_FORBIDDEN, HTTP_BAD_REQUEST
from box.utils.api import success, fail

bp = Blueprint('captcha', __name__)


# 请求手机验证码，进行用户注册
@bp.route('/api/account/code', methods=['POST'])
def request_code():
    if request.json is None:
        return fail(HTTP_BAD_REQUEST, u'缺少参数')

    mobile = request.json.get('mobile', None)
    if mobile is None:
        return fail(HTTP_BAD_REQUEST, u'手机号不能未空')

    if len(mobile) != 11:
        return fail(HTTP_BAD_REQUEST, u'手机号不合法')

    account = User.get_by_mobile(mobile)

    if account is not None:
        return fail(HTTP_BAD_REQUEST, u'手机已存在')

    if mobile_reach_ratelimit(mobile):
        return fail(HTTP_FORBIDDEN, u'验证码已发送')

    # 通过手机号请求验证码
    code = request_sms(mobile)

    if config.DEBUG:
        return success({'code': code})

    return success()
