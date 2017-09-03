# -*- coding: utf-8 -*-

from __future__ import absolute_import

import traceback

from envcfg.raw import box as config
from flask import Flask, current_app, request
from werkzeug.utils import import_string

from box.const import (HTTP_BAD_REQUEST, HTTP_FORBIDDEN,
                       HTTP_NOT_FOUND, HTTP_SERVER_ERROR)
from box.ext import db, redis
from box.utils.api import fail
from box.utils.login_manager import setup_login_manager

blueprints = [
    'box.account.view:bp',
    'box.account.view:c_bp',
    'box.captcha.view:bp',
    'box.collecation.view:bp',
    'box.order.view:bp',
    'box.product.view:bp',
    'box.pocket.view:bp',
    'box.wechat.view:bp',
    'box.admin.view:bp',
    'box.order.view:admin_bp',
    'box.collecation.view:admin_bp',
]


def create_app(name=None):
    app = Flask(name or __name__)
    app.config.from_object('envcfg.raw.box')

    app.debug = bool(int(config.DEBUG))
    app.config['TESTING'] = bool(int(config.TESTING))
    app.config['SECRET_KEY'] = config.SECRET_KEY

    db.init_app(app)
    redis.init_app(app)

    setup_login_manager(app)

    for bp_import_name in blueprints:
        bp = import_string(bp_import_name)
        app.register_blueprint(bp)

    setup_hooks(app)
    setup_error_handler(app)

    return app


def _request_log(resp, *args, **kwargs):
    is_echo_resp = bool(int(config.ECHO_API_RESPONSE))
    logger = current_app.logger
    logger.info(
        '{addr} request: [{status}] {method}, '
        'url: {url}'.format(
            addr=request.remote_addr,
            status=resp.status,
            method=request.method,
            url=request.url,
        )
    )
    if is_echo_resp and resp.mimetype == 'application/json':
        logger.info(resp.get_data())
    return resp


def setup_hooks(app):
    app.after_request(_request_log)


def setup_error_handler(app):
    @app.errorhandler(400)
    @app.errorhandler(ValueError)
    def http_bad_request(e):
        app.logger.warn(traceback.format_exc())
        return fail(HTTP_BAD_REQUEST)

    @app.errorhandler(403)
    def http_forbidden(e):
        app.logger.warn(traceback.format_exc())
        return fail(HTTP_FORBIDDEN)

    @app.errorhandler(404)
    def http_not_found(e):
        app.logger.warn(traceback.format_exc())
        return fail(HTTP_NOT_FOUND)

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def http_server_error(e):
        app.logger.error(traceback.format_exc())
        return fail(HTTP_SERVER_ERROR)
