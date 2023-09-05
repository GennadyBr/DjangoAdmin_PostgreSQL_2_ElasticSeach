# Films Django API, Django Admin, ETL, Elasticsearch
[Ссылка на проект](https://github.com/KarinaSmirnova/Async_API_sprint_1)

## start
.env файл присутствует в учебных целях

docker compose up --build

## Django
http://localhost:8000/

## Django admin
http://localhost:8000/admin
http://localhost:8000/admin/movies/filmwork/
http://localhost:8000/admin/movies/person/
http://localhost:8000/admin/movies/genre/

## API
http://127.0.0.1:8000/api/v1/movies/

## ElasticSearch
http://localhost:9200/

## ElasticSearch Movies
http://localhost:9200/movies/_search?pretty=true&q=*:*&size=1000

## ElasticSearch Genres
http://localhost:9200/genres/_search?pretty=true&q=*:*&size=1000

## ElasticSearch Persons
http://localhost:9200/persons/_search?pretty=true&q=*:*&size=1000
