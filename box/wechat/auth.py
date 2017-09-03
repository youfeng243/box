# -*- coding: utf-8 -*-

import json
from copy import deepcopy
from random import randint
from urllib import urlencode
from urlparse import ParseResult

import requests
from envcfg.raw import box as config
from flask import request, url_for, session, has_request_context, g, redirect

from box.account.model import User
from box.ext import redis
from box.utils import logger

ACCESS_TOKEN_URL = 'https://api.weixin.qq.com/cgi/bin/token'
ACCESS_TOKEN_KEY = 'box:wechat:open:access-token'

OAUTH_AUTH_URL = 'https://open.weixin.qq.com/connect/oauth2/authorize'
OAUTH_TOKEN_URL = 'https://api.weixin.qq.com/sns/oauth2/access_token'


def request_access_token():
    access_token = redis.get(ACCESS_TOKEN_KEY)
    if access_token is not None:
        return access_token

    resp = requests.get(
        ACCESS_TOKEN_URL,
        params={
            'grant_type': 'client_credential',
            'appid': config.WECHAT_APP_ID,
            'secret': config.WECHAT_APP_SECRET
        }, verify=False)

    data = json.loads(resp.content)
    access_token = data.get('access_token', None)

    if access_token is not None:
        expired = data.get('expires_in')
        redis.set(ACCESS_TOKEN_KEY, access_token, expired)

    return access_token


def get_oauth_url(endpoint, state):
    args = deepcopy(request.args.to_dict())
    args.update(request.view_args)
    url = url_for(endpoint, _external=True, **args)
    qs = urlencode({
        'appid': config.WECHAT_APP_ID,
        'redirect_uri': url,
        'scope': 'snsapi_userinfo',
        'state': state,
    })
    o = ParseResult('https', 'open.weixin.qq.com',
                    '/connect/oauth2/authorize', '',
                    query=qs, fragment='wechat_redirect')
    return o.geturl()


def get_token_url(code):
    args = deepcopy(request.args.to_dict())
    args.update(request.view_args)
    qs = urlencode({
        'appid': config.WECHAT_APP_ID,
        'secret': config.WECHAT_APP_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
    })
    o = ParseResult('https', 'api.weixin.qq.com',
                    '/sns/oauth2/access_token', '',
                    query=qs, fragment='wechat_redirect')
    return o.geturl()


def wechat_login(*args, **kwargs):
    if request.endpoint != 'wechat.index':
        openid = session.get('openid', None)
        if openid is None and has_request_context():
            code = request.args.get('code', None)
            if code is not None:
                url = get_token_url(code)
                resp = requests.get(url, verify=False)
                if resp.status_code == 200:
                    data = json.loads(resp.content)
                    openid = data.get('openid', None)
                    session['openid'] = openid
            else:
                if request.method == 'GET':
                    url = get_oauth_url(request.endpoint, randint(1, 10))
                    logger.info(url)
                    return redirect(url)
        g.wechat_openid = openid


def get_current_user():
    openid = session.get('openid', None)
    if openid is None:
        return None

    return User.get_by_openid(openid)
