import os
import json
import backoff
import psycopg
import requests

from time import sleep
from datetime import datetime
from typing import Generator
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from psycopg import ServerCursor
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

from decorators import coroutine
from logger import logger
from settings import database_settings
from models_state import JsonFileStorage, State, Movie, BaseStorage

load_dotenv()

sql_query = """
        SELECT fw.id, fw.title, fw.description, fw.rating, fw.type,
        fw.created_at, greatest(fw.updated_at, max(p.updated_at), max(g.updated_at)) as updated_at, 
        COALESCE ( json_agg( distinct jsonb_build_object( 'person_role', pfw.role, 'person_id', p.id, 
        'person_name', p.full_name ) ) FILTER (WHERE p.id is not null), '[]' ) as persons, 
        array_agg(DISTINCT g.name) as genres 
        FROM content.film_work fw 
        LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id 
        LEFT JOIN content.person p ON p.id = pfw.person_id 
        LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id 
        LEFT JOIN content.genre g ON g.id = gfw.genre_id 
        WHERE fw.updated_at >= %s or p.updated_at >= %s OR g.updated_at >= %s
        GROUP BY fw.id 
        ORDER BY updated_at ASC
"""

STATE_KEY = 'last_movies_updated'  # хранилище состояний. последний обновленный фильм


def index_prep(movie):
    """формирование индекса"""
    movie_dict_res = {
        "index": {"_index": "movies", "_id": str(movie['id'])},
        "doc": {
            "id": str(movie['id']),
            "imdb_rating": movie['rating'],
            "genre": [g for g in movie['genres']],
            "title": movie['title'],
            "description": movie['description'],
            "director": ','.join([act['person_name'] for act in movie['persons'] if
                                  act['person_role'] == 'director' or act['person_role'] == 'DR']),
            "actors_names": ','.join([act['person_name'] for act in movie['persons'] if
                                      act['person_role'] == 'actor' or act['person_role'] == 'AC']),
            "writers_names": [act['person_name'] for act in movie['persons'] if
                              act['person_role'] == 'writer' or act['person_role'] == 'WR'],
            "actors": [dict(id=act['person_id'], name=act['person_name']) for act in movie['persons'] if
                       act['person_role'] == 'actor' or act['person_role'] == 'AC'],
            "writers": [dict(id=act['person_id'], name=act['person_name']) for act in movie['persons'] if
                        act['person_role'] == 'writer' or act['person_role'] == 'WR'],
        },
        "updated_at": movie['updated_at']
    }
    return movie_dict_res


# этой корутине передаем курсор, который получаем из базы ОДИН раз.
# не тратим ресурсы на получение курсора каждый раз
@coroutine
def fetch_changed_movies(cursor, next_node: Generator) -> Generator[datetime, None, None]:
    while last_updated := (yield):  # yield принимаем datetime
        # логгер
        logger.info(f'Fetching movies changed after ' f'{last_updated}')
        # выбираем все фильмы где updated_at больше значения %s
        # %s присылается из last_updated := (yield)
        # сортируем order by updated_at что бы в следующий раз брать самую свежую запись
        # sql = 'SELECT * FROM content.film_work WHERE updated_at > %s order by updated_at asc'
        # logger.info('Fetching movies updated after %s', last_updated)
        cursor.execute(sql_query, (last_updated, last_updated, last_updated,))
        while results := cursor.fetchmany(size=100):  # передаем пачками
            next_node.send(results)  # передаем следующую корутину


@coroutine
@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError))
def transform_movies(next_node: Generator) -> Generator[list[dict], None, None]:
    # принимаем next_node корутину из предущего метода. Generator[list[dict] список из словарей
    while movie_dicts := (yield):
        batch = []
        for movie_dict in movie_dicts:  # итерируем СПИСОК из словарей
            movie_dict_prep = index_prep(movie_dict)  # трасформация данных
            movie = Movie(**movie_dict_prep)  # инициализируем BaseModel Класс Movie cо словарем как аргументом
            batch.append(movie)  # подготовка списка из Объектов Movie
        next_node.send(batch)  # передаем следующую Список из Словарей (объект Movie)


@coroutine
@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError))
def save_movies(state: State) -> Generator[list[Movie], None, None]:
    while movies := (yield):
        body = []
        for movie in movies:
            index_dict = {'index': movie.index}
            body.append(index_dict)
            body.append(movie.doc)  #
        logger.info(f'ADDED, {type(body)=} {body=}')  # логируем JSON
        res = es.bulk(operations=body, )
        logger.info(res)
        state.set_state(STATE_KEY, str(movies[-1].updated_at))
        # сохраняем последний фильм из ранее отсортированного по order by updated_at в хранилище
        # если что-то упадет, то следующий раз начнем с этого фильма.


if __name__ == '__main__':
    # start ElasticSearch
    try:
        es = Elasticsearch(os.getenv('ES_HOST_PORT'))
        # make Index ElasticSearch
        if not es.indices.exists(index='movies'):
            with open('es_schema.json', 'r') as file:
                data = json.load(file)
                es.indices.create(index='movies', body=data)
    except Exception as error:
        logger.info(
            f'{error=}, {es.info=}, {es.graph=}, {es.health_report=}, {es.logstash=}, {es.watcher=}, {es.transport=}, {es.__doc__=}')
    print('Start loading data to Elasticsearch')
    storage = JsonFileStorage(logger, 'storage.json')

    state = State(JsonFileStorage(logger=logger))  # инициализируется Класс State - сохраненное последнее состояние

    dsn = make_conninfo(**database_settings.dict())  # Merge a string and keyword params into a single conninfo string
    logger.info(f'***CONNECTING TO DATABASE XXX CONNECTING TO DATABASE XXX CONNECTING TO DATABASE***')

    with psycopg.connect(dsn, row_factory=dict_row) as conn, ServerCursor(conn, 'fetcher') as cur:
        # все что вынимаем (row_factory=dict_row) из базы сразу сохраняется в виде словаря
        # conn.cursor() вынимает из базы ВСЕ данные и забивает память КЛИЕНТА, а потом уже fetchmany разбивает на части
        # ServerCursor(conn, 'fetcher') вынимает из базы ВСЕ данные в память СЕРВЕРА. Потом придется на сервер ходить
        # ServerCursor закрывается автоматически в psycopg3
        # Closing a server-side cursor is more important than closing a client-side one
        # because it also releases the resources on the server, which otherwise might remain allocated
        # until the end of the session (memory, locks). Using the pattern: with conn.cursor():

        # Запускаем корутины они повиснут в памяти и будут ждать.
        # сначала запускаем последнюю корутину, так как в нее будет переданы данные из предыдущей корутины
        saver_coro = save_movies(state)  # сюда передаем последнее состояние state
        transformer_coro = transform_movies(next_node=saver_coro)  # сюда передаем предыдущую корутину
        fetcher_coro = fetch_changed_movies(cur, transformer_coro)  # сюда передаем предыдущую корутину и курсор

        while True:
            last_movies_updated = state.get_state(
                STATE_KEY)  # достаем (get_state) сохраненное состояние по ключу STATE_KEY
            logger.info('Starting ETL process for updates ...')

            fetcher_coro.send(state.get_state(STATE_KEY) or str(datetime.min))  # запускаем первую корутину

            sleep(10)  # вечный цирк который ждет изменений в базе. С задержкой 10 сек
