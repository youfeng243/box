#!/usr/bin/env bash

project=box

start() {
	status
	if [  $? = 1 ]; then
		echo "${project} is already running.."
		return 1
	fi

    cp -rf .env.sample .env
    export $(cat .env | xargs)

    nohup ~/venv/bin/python manage.py runserver -h 0.0.0.0 --port 5000 > nohup.txt 2>&1 &
    echo "${project} start success..."
}

stop() {
	status
	if [ $? = 0 ]; then
	    echo "${project} not running.."
	    return 0
	fi

    ps -ef | grep -v grep | grep ${project} | grep manage | awk '{print $2}' | xargs kill -9

	echo "${project} stop success..."
	return 1
}

restart() {
    stop
    sleep 1
    start
}

status() {
    pid=`ps -ef | grep -v grep | grep ${project} | grep manage | awk '{print $2}'`
    if [ -z "${pid}" ]; then
        return 0
    fi
    echo ${pid}
    return 1
}

case "$1" in
	start|stop|restart|status)
  		$1
		;;
	*)
		echo $"Usage: $0 {start|stop|status|restart|clean}"
		exit 1
esac
