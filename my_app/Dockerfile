# Укажите необходимую версию python
FROM python:3.10

# Выберите папку, в которой будут размещаться файлы проекта внутри контейнера
WORKDIR /opt/app

# Укажите порт, на котором приложение будет доступно внутри Docker-сети
EXPOSE 8000

# Заведите необходимые переменные окружения
ENV DJANGO_SETTINGS_MODULE 'config.settings'
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV UWSGI_PROCESSES 1
ENV UWSGI_THREADS 16
ENV UWSGI_HARAKIRI 240
#ENV ALLOWED_HOSTS ['DJANGO_ALLOWED_HOSTS']
ENV ALLOWED_HOSTS ['127.0.0.1']


RUN apt update && \
apt install -y vim && \
apt-get install -y python3-pip

# Скопируйте в контейнер файлы, которые редко меняются
COPY requirements.txt requirements.txt
COPY run_uwsgi.sh run_uwsgi.sh
COPY uwsgi/uwsgi.ini uwsgi.ini

# Установите зависимости
RUN  pip install -r requirements.txt

RUN  mkdir -p /var/www/static/ \
     && mkdir -p /var/www/media/ \
     && mkdir -p /opt/my_app/static/ \
     && mkdir -p /opt/my_app/media/
RUN chmod +x *.sh


# Скопируйте всё оставшееся. Для ускорения сборки образа эту команду стоит разместить ближе к концу файла.
COPY entrypoint.sh entrypoint.sh
COPY . .

ENTRYPOINT [ "bash", "./entrypoint.sh"]
