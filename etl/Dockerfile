# Укажите необходимую версию python
FROM python:3.10

# Выберите папку, в которой будут размещаться файлы проекта внутри контейнера
WORKDIR /opt/etl

# Заведите необходимые переменные окружения
ENV ALLOWED_HOSTS ["postgres_dc", "*", "127.0.0.1", "localhost", "elastic_dc"]

# Скопируйте в контейнер файлы, которые редко меняются
COPY requirements.txt requirements.txt
COPY run_uwsgi.sh run_uwsgi.sh
COPY uwsgi/uwsgi.ini uwsgi.ini

# Установите зависимости
RUN pip install --upgrade pip && pip install -r requirements.txt
RUN chmod +x *.sh

# Скопируйте всё оставшееся. Для ускорения сборки образа эту команду стоит разместить ближе к концу файла.
COPY . .

#ENTRYPOINT [ "bash", "./run_uwsgi.sh"]
ENTRYPOINT [ "python", "main.py" ]