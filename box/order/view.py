# -*- coding: utf-8 -*-
import traceback

from flask import Blueprint, request
from flask_login import login_required

from box.account.model import Address
from box.collecation.model import Collecation, Mode, gen_item_id
from box.const import (HTTP_BAD_REQUEST,
                       HTTP_UNAUTHORIZED,
                       EMSG_PARAMS_MISSING,
                       EMSG_PRODUCT_NOT_FOUND,
                       EMSG_PARAMS_ERROR, HTTP_OK)
from box.ext import db
from box.order.model import Order, OrderItem
from box.payment.model import Payment
from box.pocket.model import Pocket
from box.product.model import Product
from box.utils import logger
from box.utils.api import success, fail
from box.wechat.auth import get_current_user
from box.wechat.order import create_jsapi_params

bp = Blueprint('order', __name__)

# 后台管理接口
admin_bp = Blueprint('admin_order', __name__)

EXPRESS_FEE = 0


# 获取订单数目接口
@admin_bp.route('/admin/orders/<int:status>', methods=['GET'])
@login_required
def get_order_num(status):
    try:
        return success(Order.get_order_num(status))
    except:
        logger.error("查询数据数目接口失败: status = {} {}".format(status, traceback.format_exc()))
    return fail(HTTP_OK, u"订单数目查询失败")


# 分页数据查询接口
@admin_bp.route('/admin/orders', methods=['POST'])
@login_required
def get_order_list():
    # json = {
    #     'page': 1,
    #     'size': 10,
    #     'status': 100,
    # }

    if request.json is None:
        return fail(HTTP_OK, EMSG_PARAMS_MISSING)

    page = request.json.get('page')
    size = request.json.get('size')
    status = request.json.get('status')

    if not isinstance(page, int) or \
            not isinstance(size, int) or \
            not isinstance(status, int):
        logger.error("请求参数错误: page = {} size = {} status = {}".format(
            page, size, status))
        return fail(HTTP_OK, EMSG_PARAMS_ERROR)

    # 请求参数必须为正数
    if page <= 0 or size <= 0:
        msg = "请求参数错误: page = {} size = {} status = {}".format(
            page, size, status)
        logger.error(msg)
        return fail(HTTP_OK, msg)

    result_list = Order.get_order_list(page, status, size)
    return success(result_list)


# 增加删除订单接口
@admin_bp.route('/admin/orders/<int:order_id>', methods=['DELETE'])
@login_required
def delete_order(order_id):
    msg = u"删除订单失败: {}".format(order_id)
    try:
        is_success, msg = Order.delete(order_id)
        if is_success:
            return success(msg)
    except:
        logger.error("删除订单异常: {}".format(traceback.format_exc()))

    return fail(HTTP_OK, msg)


# 修改物流接口
@admin_bp.route('/admin/orders/logistics', methods=['PUT'])
@login_required
def update_order_logistics():
    if request.json is None:
        return fail(HTTP_OK, EMSG_PARAMS_MISSING)

    logistics_no = request.json.get('logistics_no')
    order_id = request.json.get('id')

    is_success, msg = Order.update_logistics(order_id, logistics_no)

    if is_success:
        return success(msg)

    return fail(HTTP_OK, msg)


# 编辑用户信息
@admin_bp.route('/admin/orders/userinfo', methods=['PUT'])
@login_required
def update_user_info():
    if request.json is None:
        return fail(HTTP_OK, EMSG_PARAMS_MISSING)

    username = request.json.get('username')
    mobile = request.json.get('mobile')
    address = request.json.get('address')
    order_id = request.json.get('id')

    is_success, msg = Order.update_user_info(order_id, username, mobile, address)

    if is_success:
        return success(msg)

    return fail(HTTP_OK, msg)


# 邮寄费用接口
@bp.route('/api/express/price', methods=['GET'])
def express():
    return success(EXPRESS_FEE)


# 创建购买箱子订单  有BUG，现金支付在网络不稳定的情况下可能会造成多次付费
@bp.route('/api/orders', methods=['POST'])
def create_order():
    current_user = get_current_user()

    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')

    user_id = current_user.id

    if request.json is None:
        return fail(HTTP_BAD_REQUEST, EMSG_PARAMS_MISSING)

    # 产品ID？
    product_id = request.json.get('product_id')

    # 得先判断产品是否存在，你请求个没有的产品肯定不行
    product = Product.get(product_id)

    if product is None:
        return fail(HTTP_BAD_REQUEST, EMSG_PRODUCT_NOT_FOUND)

    # 地址ID
    address_id = request.json.get('address_id')

    # 支付方式
    payment_method = request.json.get('payment_method') or 'wechat'

    address = Address.get(address_id)
    if address is None:
        return fail(HTTP_BAD_REQUEST, EMSG_PARAMS_ERROR)

    if address.user_id != user_id:
        return fail(HTTP_BAD_REQUEST, EMSG_PARAMS_ERROR)

    # 买了多个箱子
    box_num = int(request.json.get('count'))
    if box_num <= 0:
        logger.warn("箱子数目不正确: {}".format(box_num))
        return fail(HTTP_BAD_REQUEST, u"箱子数目不正确")

    # 计算箱子的费用
    product_fee = product.price * box_num

    # 邮寄费用默认为0
    express_fee = EXPRESS_FEE

    order = Order.create(
        user_id=user_id,
        address_id=address_id,
        product_fee=product_fee,
        express_fee=express_fee,
        box_num=box_num
    )

    items = []
    for each in range(box_num):
        item = OrderItem.create(
            user_id=user_id,
            product_id=product_id,
            order_id=order.id
        )
        items.append(item)

    # 总费用
    total_fee = product_fee + express_fee

    is_success, rv = False, None

    if payment_method == Order.PAYED_WECHAT:
        payment = Payment.create(
            user_id=user_id,
            amount=total_fee,
            payment_type=Payment.TYPE_BUY,
        )

        order.payment_id = payment.id
        db.session.add(order)
        db.session.commit()

        # 这里是微信支付的流程
        is_success, rv = create_jsapi_params(current_user.openid, payment)

    elif payment_method == Order.PAYED_CRASH:
        pocket = Pocket.get_or_create_by_user_id(user_id)
        if pocket.balance >= total_fee:
            pocket.cut_down(total_fee)
            db.session.commit()

            # 不明白为什么现金买的 就有详细订单，微信支付的就没有详细订单了
            for each in items:
                item_id = gen_item_id(user_id)
                Collecation.create(
                    user_id=user_id,
                    mode_id=Mode.get_default_id(),
                    item_id=item_id)
                each.item_id = item_id
                db.session.add(each)

            order.status = Order.STATUS_PAYED
            order.payment_method = payment_method
            db.session.add(order)
            is_success = True
        else:
            return fail(HTTP_BAD_REQUEST,
                        u'您当前余额为 %0.2f 元，不足以支付此订单' %
                        (pocket.balance * 1.0 / 100))

    if is_success:
        return success(rv)
    else:
        if rv:
            logger.warn(rv)
        return fail(HTTP_BAD_REQUEST, u'购买失败')
