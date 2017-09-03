# -*- coding: utf-8 -*-
import traceback
from datetime import datetime

from flask import Blueprint, request
from flask_login import login_required

from box.collecation.model import Collecation, Mode
from box.const import HTTP_UNAUTHORIZED, HTTP_BAD_REQUEST, HTTP_SERVER_ERROR, HTTP_OK, EMSG_PARAMS_MISSING, \
    EMSG_PARAMS_ERROR
from box.ext import db
from box.pocket.model import Pocket
from box.utils import logger
from box.utils.api import success, fail
from box.wechat.auth import wechat_login, get_current_user

bp = Blueprint('collecation', __name__)
bp.before_request(wechat_login)

# 后台管理接口
admin_bp = Blueprint('admin_collection', __name__)


# 获取订单数目接口
@admin_bp.route('/admin/collection/num', methods=['POST'])
@login_required
def get_collection_num():
    # json = {
    #     'stage': 100,
    #     'put_in_status': 100,
    # }
    if request.json is None:
        return fail(HTTP_OK, u"参数错误")

    stage = request.json.get('stage')
    put_in_status = request.json.get('put_in_status')
    if stage is None or put_in_status is None:
        return fail(HTTP_OK, u"参数错误")

    try:
        return success(Collecation.get_collection_num(stage, put_in_status))
    except:
        logger.error(
            "查询数据数目接口失败: stage = {} put_in_status = {} {}".format(
                stage, put_in_status, traceback.format_exc()))
    return fail(HTTP_OK, u"获取存储订单数目查询失败")


# 分页数据查询接口
@admin_bp.route('/admin/collection', methods=['POST'])
@login_required
def get_collection_list():
    # json = {
    #     'page': 1,
    #     'size': 10,
    #     'put_in_status': 100,
    #     'stage': 100,
    # }

    if request.json is None:
        return fail(HTTP_OK, EMSG_PARAMS_MISSING)

    page = request.json.get('page')
    size = request.json.get('size')
    stage = request.json.get('stage')
    put_in_status = request.json.get('put_in_status')

    if not isinstance(page, int) or \
            not isinstance(size, int) or \
            not isinstance(stage, int):
        logger.error("请求参数错误: page = {} size = {} stage = {} put_in_status = {}".format(
            page, size, stage, put_in_status))
        return fail(HTTP_OK, EMSG_PARAMS_ERROR)

    # 请求参数必须为正数
    if page <= 0 or size <= 0:
        msg = "请求参数错误: page = {} size = {} stage = {} put_in_status = {}".format(
            page, size, stage, put_in_status)
        logger.error(msg)
        return fail(HTTP_OK, msg)

    result_list = Collecation.get_collection_list(page, stage, put_in_status, size)
    return success(result_list)


# 删除存储订单接口
@admin_bp.route('/admin/collection/<int:c_id>', methods=['DELETE'])
@login_required
def delete_order(c_id):
    msg = u"删除订单失败: {}".format(c_id)
    try:
        is_success, msg = Collecation.delete(c_id)
        if is_success:
            return success(msg)
    except:
        logger.error("删除订单异常: {}".format(traceback.format_exc()))

    return fail(HTTP_OK, msg)


# 更新阶段状态
@admin_bp.route('/admin/collection/stage', methods=['PUT'])
@login_required
def update_stage():
    # json = {
    #     'stage': 100,
    #     'id': 1,
    # }
    if request.json is None:
        return fail(HTTP_OK, EMSG_PARAMS_MISSING)

    stage = request.json.get('stage')
    c_id = request.json.get('id')

    is_success, msg = Collecation.update_stage(c_id, stage)
    if is_success:
        return success(msg)
    return fail(HTTP_OK, msg)


# 更新修改入库状态状态
@admin_bp.route('/admin/collection/store', methods=['PUT'])
@login_required
def update_store():
    # json = {
    #     'goods_address': '423-10',
    #     'id': 1,
    # }
    if request.json is None:
        return fail(HTTP_OK, EMSG_PARAMS_MISSING)

    goods_address = request.json.get('goods_address')
    c_id = request.json.get('id')

    is_success, msg = Collecation.put_in(c_id, goods_address)
    if is_success:
        return success(msg)
    return fail(HTTP_OK, msg)


# 获得所有已经存储的订单
@bp.route('/api/current/collecation')
def collecation():
    current_user = get_current_user()
    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')
    collecations = Collecation.get_multi_by_user(current_user.id)
    collecations = [each.as_resp() for each in collecations]
    return success(collecations)


# 获得存储所有收费方式
@bp.route('/api/collecation/mode')
def mode():
    mode = [each.as_resp() for each in Mode.get_all()]
    return success(mode)


# 开始下单存储，也就是点击存储下单按钮
@bp.route('/api/current/collecation/_bulk', methods=['PUT'])
def use_collecation():
    current_user = get_current_user()
    if current_user is None:
        return fail(HTTP_UNAUTHORIZED, u'请使用微信客户端登录')

    if request.json is None:
        return fail(HTTP_BAD_REQUEST, u'缺少参数')

    # 存储计费方式 现在默认是2块钱一天
    mode_id = request.json.get('mode_id')
    mode = Mode.get(mode_id)
    if mode is None:
        return fail(HTTP_BAD_REQUEST, u'参数错误')

    collecations = request.json.get('collecations')

    for each in collecations:
        id_ = each.get('id', None)
        if id_ is None:
            return fail(HTTP_BAD_REQUEST, u'参数错误')

    # 获得钱包信息
    pocket = Pocket.get_or_create_by_user_id(current_user.id)
    if pocket is None:
        return fail(HTTP_SERVER_ERROR, u'获取钱包信息失败')

    # 获取总金钱数目
    balance = pocket.balance
    total_fee = 0

    collection_list = []
    for each in collecations:
        c = Collecation.get(each.get('id'))
        if c is None:
            continue
        if c.status == Collecation.STATUS_USING:
            continue
        c.mode_id = mode_id
        c.status = Collecation.STATUS_USING

        # 存储入库时间
        c.requested_at = datetime.utcnow()

        # 用户添加的备注信息
        c.remark = each.get('remark')

        # 算总共需要的额度
        total_fee += Mode.get_mode_fee(mode_id)

        collection_list.append(c)

    # 如果总的消费大于余额  则不进行存储
    if total_fee > balance:
        return fail(HTTP_BAD_REQUEST,
                    u'您当前余额为 %0.2f 元，不足以支付此订单' %
                    (pocket.balance * 1.0 / 100))

    # todo 求所有箱子的剩余天数
    # # 算出剩下来的钱
    # remain_fee = balance - total_fee
    #
    # # 计算已经入库的所有箱子的费用
    # coll_list = Collecation.get_used_coll_by_user(current_user.id)
    # cost_
    # for item in coll_list:

    # 开始存储订单
    for item in collection_list:
        db.session.add(item)
    db.session.commit()

    return success()
