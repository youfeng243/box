#!/usr/bin/env bash

pip install virtualenv

virtualenv ~/venv
~/venv/bin/pip install -U pip
~/venv/bin/pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
cp -rf .env.sample .env
export $(cat .env | xargs)



~/venv/bin/python manage.py syncdb
echo "数据库初始化完成..."