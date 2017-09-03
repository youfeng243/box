# -*- coding: utf-8 -*-

from flask import Blueprint

from box.product.model import Product
from box.utils.api import success

bp = Blueprint('product', __name__)


# 产品列表
@bp.route('/api/products')
def products():
    product_list = [x.as_resp() for x in Product.get_all()]
    return success(product_list)
