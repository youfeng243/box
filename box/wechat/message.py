# -*- coding: utf-8 -*-

from lxml import etree


class WeChatMessage(object):
    def __init__(self, data):
        self.data = data

    @classmethod
    def parse(cls, data):
        parse_data = etree.fromstring(data)
        return WeChatMessage(parse_data)

    @property
    def openid(self):
        return self.FromUserName

    def __getattr__(self, name):
        data = self.data.find(name)
        if data is not None:
            return data.text
        return None
