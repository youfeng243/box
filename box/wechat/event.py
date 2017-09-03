# -*- coding: utf-8 -*-

from box.wechat.message import WeChatMessage


def parse_data(data):
    msg = WeChatMessage.parse(data)
    return msg


def handle_events(request_data):
    return 'success'
