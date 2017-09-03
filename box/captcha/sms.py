# -*- coding: utf-8 -*-

import json

import requests
from envcfg.raw import box as config
from requests_futures.sessions import FuturesSession

from box.corelib.leancloud import LeanCloud
from box.ext import redis
from box.utils import logger

# 一个手机号一分钟只能发一次验证码请求
DEFAULT_MOBILE_EXPIRED = 60  # 1 minute
LEANCLOUD_HOST = 'https://api.leancloud.cn'
REQUEST_SMS_CODE_URL = ''.join([LEANCLOUD_HOST, '/1.1/requestSmsCode'])
VERIFY_SMS_CODE = ''.join([LEANCLOUD_HOST,
                           '/1.1/verifySmsCode/{captcha}'])
lean_cloud_client = LeanCloud(config.LEANCLOUD_ID, config.LEANCLOUD_KEY)

DEBUG_CODE = '123456'


def _default_callback(session, resp):
    logger.info('requestSms Resp: %s', resp.json())


# 短信验证码服务
def request_sms(mobile, callback=None):
    if config.DEBUG:
        return DEBUG_CODE

    cb = callback or _default_callback
    data = {'mobilePhoneNumber': mobile}
    logger.info('requestSms: %s', mobile)
    headers = lean_cloud_client.gen_headers()
    logger.info('headers: %s', headers)
    if not int(config.LEANCLOUD_PUSH_ENABLED):
        logger.info('DO NOT requestSms')
        return None
    session = FuturesSession()
    session.post(
        REQUEST_SMS_CODE_URL,
        headers=headers,
        data=json.dumps(data),
        timeout=10,
        background_callback=cb)


# 这里是校验手机验证码
def validate_captcha(mobile, captcha):
    if config.DEBUG or config.TESTING:
        if captcha == DEBUG_CODE:
            return True
        else:
            return False

    elif not config.LEANCLOUD_ID or not config.LEANCLOUD_KEY:
        raise RuntimeError('undefined leancloud id/key')
    URL = VERIFY_SMS_CODE.format(captcha=captcha)
    resp = requests.post(
        URL,
        params={'mobilePhoneNumber': mobile},
        headers=lean_cloud_client.gen_headers(),
    )
    data = resp.json()
    rt = data.get('code', None)
    logger.info('veriftySms(%s): %s', mobile, data)
    return rt is None


# 记录当前手机号码已经发过一次验证码，存入redis 一分钟后过期
def mobile_reach_ratelimit(mobile):
    if config.DEBUG:
        return False
    key = 'box:ratelimit:mobile:captcha:%s' % mobile
    value = redis.get(key)
    logger.info('redis[%s]: %s', key, value)
    if value is not None:
        return True
    redis.setex(key, DEFAULT_MOBILE_EXPIRED, mobile)
    return False
