# -*- coding: utf-8 -*-

from flask import Blueprint

bp = Blueprint('payment', __name__)


# 不知道这个接口有没有使用。。
@bp.route('/api/payment')
def payment():
    pass
