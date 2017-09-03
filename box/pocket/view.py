# -*- coding: utf-8 -*-

from flask import Blueprint, request

from box.const import HTTP_UNAUTHORIZED, HTTP_BAD_REQUEST
from box.payment.model import Payment
from box.pocket.model import Pocket
from box.utils import logger
from box.utils.api import success, fail
from box.wechat.auth import get_current_user
from box.wechat.order import create_jsapi_params

bp = Blueprint('pocket', __name__)


# 获得用户钱包信息
@bp.route('/api/current/pocket', methods=['GET'])
def pocket():
    current_user = get_current_user()

    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')

    user_id = current_user.id

    pocket = Pocket.get_or_create_by_user_id(user_id)

    return success(pocket.as_resp())


# 充值
@bp.route('/api/current/pocket/recharge', methods=['POST'])
def recharge():
    current_user = get_current_user()

    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')

    if request.json is None:
        return fail(HTTP_BAD_REQUEST, u'缺少参数')

    amount = request.json.get('amount')

    if amount is None:
        return fail(HTTP_BAD_REQUEST, u'参数为空')

    try:
        amount = int(amount)
    except Exception:
        return fail(HTTP_BAD_REQUEST, u'充值金额错误')

    amount = int(amount)
    if amount < 1:
        return fail(HTTP_BAD_REQUEST, u'请输入充值金额')

    user_id = current_user.id

    payment = Payment.create(user_id=user_id, amount=amount,
                             payment_type=Payment.TYPE_RECHARGE)

    # 开始进行微信支付
    is_success, rv = create_jsapi_params(current_user.openid, payment)
    if is_success:
        return success(rv)
    else:
        logger.warn(rv)
        return fail(HTTP_BAD_REQUEST, u'充值失败')
