#!/usr/bin/env bash

#echo ">>>LOAD ELASTICSEARCH"
#python main.py
#docker exec new_admin_panel_sprint_3-etl_dc-1 python main.py #запуск через Bash внутри контейнера


set -e

chown www-data:www-data /var/log

uwsgi --strict --ini /opt/etl/uwsgi.ini
