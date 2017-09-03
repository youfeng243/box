# -*- coding: utf-8 -*-

from __future__ import absolute_import

from flask_sqlalchemy import SQLAlchemy

from box.corelib.redis import Redis

db = SQLAlchemy()
redis = Redis()
