#!/bin/sh

#echo "Start venv"
#source venv/bin/activate
#
#echo "Stop apache2"
#service apache2 stop
#
#echo "DOWN Docker Compose"
#docker compose down
#
#echo "UP Docker Compose"
#docker compose up -d --build
#
#echo "List-up Docker"
#docker ps -a

#echo "Apply database makemigrations"
#my_app/python manage.py makemigrations

#echo "Apply database migrate"
#my_app/python manage.py migrate

#echo "Create superuser"
#my_app/python manage.py createsuperuser --username gennady --email gennady.budazhapov@gmail.com

#echo "Collect static files"
#my_app/python manage.py collectstatic --noinput

#echo "Start uWSGI"
#uwsgi --strict --ini uwsgi.ini

echo "Starting server"
my_app/python manage.py runserver
