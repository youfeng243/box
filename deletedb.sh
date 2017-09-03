#!/usr/bin/env bash

cp -rf .env.sample .env
export $(cat .env | xargs)

~/venv/bin/python manage.py deletedb
echo "数据库删除完成..."