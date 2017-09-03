# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask_script import Manager
from setuptools import find_packages

from box.admin.model import Admin
from box.app import create_app
from box.collecation.model import Mode
from box.ext import db
from box.product.model import Product

application = create_app('box')
manager = Manager(application)


def _import_models():
    puff_packages = find_packages('./box')
    for each in puff_packages:
        guess_module_name = 'box.%s.model' % each
        try:
            __import__(guess_module_name, globals(), locals())
            print 'Find model:', guess_module_name
        except ImportError:
            pass


@manager.command
def syncdb():
    with application.test_request_context():
        _import_models()

        db.create_all()
        db.session.commit()

        # 管理员
        admin = Admin.create('youfeng', '555556')
        admin.save()

        # 产品
        product = Product(name='定制防潮防水纸箱', price=1, description='413mmx320mmx257mm')
        product.save()

        # 存储费用
        mode = Mode(name='普通', price=1, description='普通')
        mode.save()

    print 'Database Created'


@manager.command
def deletedb():
    with application.test_request_context():
        _import_models()

        db.drop_all()
        db.session.commit()

    print 'Database deleted'


@manager.command
def dropdb():
    with application.test_request_context():
        db.drop_all()
    print 'Database Dropped'


if __name__ == '__main__':
    manager.run()
