# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json

from flask import Response

from box.const import HTTP_OK, ERROR_MSG


# 构造response
def json_resp(data, http_status):
    return Response(data, status=http_status, mimetype="application/json")


# 返回成功
def success(result=None, **kwargs):
    resp = {
        'success': True,
        'error': None,
        'result': result
    }
    if kwargs:
        resp.update(kwargs)
    data = json.dumps(resp)
    return json_resp(data, HTTP_OK)


# 返回失败
def fail(http_status, error=None):
    resp = {
        'success': False,
        'error': error or ERROR_MSG.get(http_status, "undefined error"),
        'result': None
    }
    data = json.dumps(resp)
    return json_resp(data, http_status)
