# Сервис полнотекстового поиска по фильмам

[Ссылка на проект](https://github.com/GennadyBr/PostgreSQL_2_ElasticSeach)

**проект создан для демонстрации Airflow, со следующими фичами**
- миграция из SQLite в Postgresql
- Django Admin для редактирования PostgreSQL
- Django API
- миграция из Postgresql в Elasticseach для организации полнотекстового поиска по данным
- отслеживание изменений в Postgresql и авто обновление Elasticseach
- веб-сервер NGINX
- логирование с помощью logging
- линтер flake8
- .env и docker-compose.override.yml присутствуют в демонстрационных целях
- проект упакован в Docker Compose и запущен на VPS

## Проект уже запущен на сайте
## Django
http://5.35.83.245:8000/

## Django admin
http://5.35.83.245:8000/admin

## Django admin - фильмы
http://5.35.83.245:8000/admin/movies/filmwork/

## Django admin - персоны
http://5.35.83.245:8000/admin/movies/person/

## Django admin - жанры
http://5.35.83.245:8000/admin/movies/genre/

## Вывод фильмов с пагинацией
http://5.35.83.245:8000/api/v1/movies/

## ElasticSearch
http://5.35.83.245:9201/

## ElasticSearch фильмы
http://5.35.83.245:9201/movies/_search?pretty=true&q=*:*&size=1000

## ElasticSearch жанры
http://5.35.83.245:9201/genres/_search?pretty=true&q=*:*&size=1000

## ElasticSearch персоны
http://5.35.83.245:9201/persons/_search?pretty=true&q=*:*&size=1000
