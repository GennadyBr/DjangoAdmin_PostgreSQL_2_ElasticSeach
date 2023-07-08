#!/bin/bash

echo "Waiting for postgres..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo ">>>MIGRATE database"
python manage.py migrate
echo ">>>STATIC files collect"
python manage.py collectstatic --noinput


echo ">>>CREATESUPERUSER"

DJANGO_SUPERUSER_USERNAME=admin \
DJANGO_SUPERUSER_PASSWORD=123123 \
DJANGO_SUPERUSER_EMAIL=mail@mail.ru \
python manage.py createsuperuser --noinput


echo ">>>LOAD DATA"
cd sqlite_to_postgres
python load_data.py

echo ">>>Start runserver"
cd ..
python manage.py runserver 0.0.0.0:8000

#bash run_uwsgi.sh