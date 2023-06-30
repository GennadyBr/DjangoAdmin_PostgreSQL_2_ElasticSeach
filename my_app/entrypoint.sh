#!/bin/sh
echo ">>>Apply database migrate"
cd my_app
python manage.py migrate
echo ">>>Collect static files"
python manage.py collectstatic --noinput
echo ">>>Compile messages"
django-admin compilemessages
echo ">>>Create superuser"
python manage.py createsuperuser \
    --noinput \
    --username gennady
echo ">>>Start runserver"
python manage.py runserver
