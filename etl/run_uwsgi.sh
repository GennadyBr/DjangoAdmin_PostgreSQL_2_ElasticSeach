#!/usr/bin/env bash

echo ">>>LOAD ELASTICSEARCH"
python main.py
#docker exec sprint_3_1-etl_dc-1 python main.py #запуск через Bash внутри контейнера


set -e

chown www-data:www-data /var/log

uwsgi --strict --ini /opt/etl/uwsgi.ini
