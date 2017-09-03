# -*- coding: utf-8 -*-

import time

import requests
from dicttoxml import dicttoxml
from envcfg.raw import box as config
from flask import url_for, request
from lxml import etree

from box.wechat.signature import signature_mch_info, get_nonce_str

CREATE_ORDER_URL = 'https://api.mch.weixin.qq.com/pay/unifiedorder'
QUERY_ORDER_URL = 'https://api.mch.weixin.qq.com/pay/orderquery'


class XMLData(object):
    def __init__(self, data):
        self.data = data

    @classmethod
    def parse(cls, data):
        parsed_data = etree.fromstring(data)
        return cls(parsed_data)

    def __getattr__(self, name):
        value = self.data.find(name)
        if value is not None:
            return value.text
        return None


def request_wechat_order(openid, order_id, body, price_in_fen):
    NOTIFY_URL = url_for('wechat.callback', _external=True)
    params = {
        'appid': config.WECHAT_APP_ID,
        'mch_id': config.WECHAT_MCH_ID,
        'openid': openid,
        'device_info': 'WEB',
        'nonce_str': get_nonce_str(n=32),
        'body': body,
        'out_trade_no': order_id,
        'total_fee': price_in_fen,
        'spbill_create_ip': request.remote_addr,
        'notify_url': NOTIFY_URL,
        'trade_type': 'JSAPI',
    }
    sign = signature_mch_info(params)

    params['sign'] = sign

    xml_data = dicttoxml(params)

    resp = requests.post(CREATE_ORDER_URL, data=xml_data)

    data = XMLData.parse(resp.content)

    return data


# weixin pay interface
def create_jsapi_params(openid, payment):
    resp = request_wechat_order(
        openid, payment.payment_no,
        u'Account Recharge', payment.amount)

    if resp.return_code == 'SUCCESS' and resp.result_code == 'SUCCESS':
        prepay_id = resp.prepay_id
        rv = {'appId': config.WECHAT_APP_ID,
              'timeStamp': str(int(time.time())),
              'nonceStr': 'abcd',
              'package': 'prepay_id=%s' % prepay_id,
              'signType': 'MD5'}
        sign = signature_mch_info(rv)
        rv['paySign'] = sign
        return True, rv
    else:
        return False, resp


# 查询微信订单信息 回调
def query_order_from_wechat(transaction_id):
    params = {
        'appid': config.WECHAT_APP_ID,
        'mch_id': config.WECHAT_MCH_ID,
        'transaction_id': transaction_id,
        'nonce_str': get_nonce_str(31),
    }
    sign = signature_mch_info(params)
    params['sign'] = sign

    data = dicttoxml(params)

    resp = requests.post(QUERY_ORDER_URL, data)

    data = XMLData.parse(resp.content)

    return data
