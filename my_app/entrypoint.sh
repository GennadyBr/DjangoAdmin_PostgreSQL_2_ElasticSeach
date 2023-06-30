#!/bin/bash
echo ">>>MIGRATE database"
python manage.py migrate
echo ">>>STATIC files collect"
python manage.py collectstatic --noinput
echo ">>>COMPILE messages"
django-admin compilemessages
echo ">>>CREATESUPERUSER"
python manage.py createsuperuser \
    --noinput \
    --username gennady

echo ">>>Start runserver"
python manage.py runserver
