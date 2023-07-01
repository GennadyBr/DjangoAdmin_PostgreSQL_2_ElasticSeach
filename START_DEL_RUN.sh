#!/bin/bash
echo ">>>DOWN all containers"
docker compose down
echo ">>>VENV activate"
source venv/bin/activate
echo ">>>KILL apache2"
sudo service apache2 stop
echo ">>>KILL all systems containers"
docker system prune -f
#echo ">>>KILL all volumes containers"
#docker volume rm sprint_3_1_media_volume sprint_3_1_postgres_data sprint_3_1_static_volume
echo ">>>BUILD UP all containers"
docker compose up --build

