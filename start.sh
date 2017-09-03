#!/usr/bin/env bash

cp -rf .env.sample .env
export $(cat .env | xargs)

nohup ~/venv/bin/python manage.py runserver -h 0.0.0.0 --port 5000 > nohup.txt 2>&1 &
echo "启动完成..."