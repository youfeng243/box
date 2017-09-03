#!/usr/bin/env python
# encoding: utf-8
"""
@author: youfeng
@email: youfeng243@163.com
@license: Apache Licence
@file: view.py
@time: 2017/9/2 19:33
"""
from flask import Blueprint
from flask import request
from flask_login import login_required
from flask_login import login_user, logout_user

from box.admin.model import Admin
from box.const import HTTP_BAD_REQUEST, EMSG_PARAMS_MISSING, EMSG_PARAMS_ERROR, HTTP_UNAUTHORIZED
from box.utils import logger
from box.utils.api import fail, success

bp = Blueprint('admin_account', __name__)


@bp.route('/admin/login', methods=['POST'])
def admin_login():
    if request.json is None:
        logger.warn("参数错误...")
        return fail(HTTP_BAD_REQUEST, EMSG_PARAMS_MISSING)

    username = request.json.get('username', None)
    password = request.json.get('password', None)
    if username is None or password is None:
        logger.warn("用户账号密码没有传过来...")
        return fail(HTTP_UNAUTHORIZED, EMSG_PARAMS_ERROR)

    admin = Admin.get_admin_by_username(username)
    if admin is None:
        logger.warn("当前用户不存在: {}".format(username))
        return fail(HTTP_UNAUTHORIZED, u"当前用户不存在")

    if admin.password != password:
        logger.warn("当前用户密码错误: {} {}".format(username, password))
        return fail(HTTP_UNAUTHORIZED, u"密码错误!")

    # 登录用户信息
    login_user(admin, remember=True)

    logger.info("登录成功: {}".format(username))
    return success(admin.as_resp())


@bp.route('/admin/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return success(u"登出成功!")


@bp.route('/admin/test', methods=['GET'])
@login_required
def admin_test():
    logger.info("当前属于登录状态...")
    return success(u"测试通过!")
