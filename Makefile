upvm:
	sudo docker-compose up -d --build

downvm:
	sudo docker-compose down --remove-orphans

psvm:
	sudo docker-compose ps

up:
	docker compose up -d --build

down:
	docker compose down --remove-orphans

ps:
	docker compose ps

venv:
	sudo python3.11 -m venv venv

net:
	sudo docker network create nginx_proxy

5433:
	sudo lsof -i -P -n | grep 5433

8000:
	sudo lsof -i -P -n | grep 8000

9200:
	sudo lsof -i -P -n | grep 9200

log:
	sudo docker logs backend
