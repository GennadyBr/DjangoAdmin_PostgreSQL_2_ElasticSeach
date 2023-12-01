FROM python:3.11

WORKDIR /opt/etl

ENV ALLOWED_HOSTS ["postgres_dc", "*", "127.0.0.1", "localhost", "elastic_dc"]

COPY requirements.txt requirements.txt
COPY run_uwsgi.sh run_uwsgi.sh
COPY uwsgi/uwsgi.ini uwsgi.ini

RUN pip install --upgrade pip && pip install -r requirements.txt
RUN chmod +x *.sh

COPY . .

#ENTRYPOINT [ "bash", "./run_uwsgi.sh"]
ENTRYPOINT [ "python", "main.py" ]