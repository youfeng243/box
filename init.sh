#!/usr/bin/env bash

HOST_NAME="127.0.0.1"
PORT="3306"
USERNAME="root"
PASSWORD="000000"

DBNAME="dkw"
create_db_sql="create database IF NOT EXISTS ${DBNAME}"

mysql -h${HOST_NAME}  -P${PORT}  -u${USERNAME} -p${PASSWORD} -e "${create_db_sql}"

apt-get install libmysqlclient-dev
pip install virtualenv

virtualenv ~/venv
~/venv/bin/pip install -U pip
~/venv/bin/pip install -r requirements.txt -i http://pypi.douban.com/simple --trusted-host pypi.douban.com
cp -rf .env.sample .env
export $(cat .env | xargs)



~/venv/bin/python manage.py syncdb
echo "数据库初始化完成..."