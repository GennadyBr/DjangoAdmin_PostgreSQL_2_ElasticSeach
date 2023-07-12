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
#docker volume rm new_admin_panel_sprint_3_media_volume new_admin_panel_sprint_3_postgres_data new_admin_panel_sprint_3_static_volume
echo ">>>BUILD UP all containers"
docker compose up --build

