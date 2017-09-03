# -*- coding: utf-8 -*-

import hashlib
import random
import string
from functools import wraps

from envcfg.raw import box as config
from flask import request

from box.const import HTTP_FORBIDDEN
from box.utils import logger
from box.utils.api import fail


def _generate_signature(timestamp, nonce, token):
    array = [timestamp, nonce, token]
    array = sorted(array)
    sig_str = ''.join(array)
    signature = hashlib.sha1(sig_str).hexdigest()
    return signature


def check_signature(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        signature = request.args.get('signature', '')
        timestamp = request.args.get('timestamp', '')
        nonce = request.args.get('nonce', '')

        token = config.WECHAT_TOKEN

        cal_signature = _generate_signature(timestamp, nonce, token)
        if not cal_signature == signature:
            logger.warn("%s != %s" % (signature, cal_signature))
            return fail(HTTP_FORBIDDEN)

        return func(*args, **kwargs)

    return decorator


def signature_mch_info(params):
    args = params.items()
    result = sorted(args, cmp=lambda x, y: cmp(x[0], y[0]))
    result = ['%s=%s' % (key, value) for key, value in result if value != '']
    to_hash = '%s&key=%s' % ('&'.join(result), config.WECHAT_PAYMENT_SECRET)
    hashed = hashlib.md5(to_hash).hexdigest()
    return hashed.upper()


def get_nonce_str(n):
    return ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for _ in range(n))
