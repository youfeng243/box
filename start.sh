#!/usr/bin/env bash

pip install virtualenv

virtualenv ~/venv
~/venv/bin/pip install -U pip
~/venv/bin/pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
cp -rf .env.sample .env
export $(cat .env | xargs)

nohup ~/venv/bin/python manage.py runserver -h 0.0.0.0 --port 5000 > nohup.txt 2>&1 &
echo "启动完成..."