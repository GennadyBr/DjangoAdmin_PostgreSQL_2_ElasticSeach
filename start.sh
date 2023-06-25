#!/bin/sh

echo "Start venv"
source venv/bin/activate

echo "Stop apache2"
service apache2 stop

echo "DOWN Docker Compose"
docker compose down

echo "UP Docker Compose"
docker compose up -d --build

echo "List-up Docker"
docker ps -a

#echo "Apply database makemigrations"
#python my_app/manage.py makemigrations

#echo "Apply database migrate"
#python my_app/manage.py migrate

#echo "Create superuser"
#python my_app/manage.py createsuperuser --username gennady --email gennady.budazhapov@gmail.com

#echo "Collect static files"
#python my_app/manage.py collectstatic --noinput

#echo "Start uWSGI"
#uwsgi --strict --ini uwsgi.ini

echo "Starting server"
python my_app/manage.py runserver
