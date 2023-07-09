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
from models_state import JsonFileStorage, State, Base_Model, BaseStorage

load_dotenv()

sql_query_movies = """
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
        WHERE fw.updated_at >= %s
        GROUP BY fw.id 
        ORDER BY updated_at ASC
"""

sql_query_genres = """
        SELECT g.id, g.name, g.description, g.created_at, g.updated_at, 
        STRING_AGG(DISTINCT fw.id::text, ', ') as film_ids 
        FROM content.genre g 
        LEFT JOIN content.genre_film_work gfw ON gfw.genre_id = g.id 
        LEFT JOIN content.film_work fw ON fw.id = gfw.film_work_id 
        WHERE g.updated_at >= %s 
        GROUP BY g.id 
        ORDER BY updated_at ASC;
"""

# sql_query_genres = """
#         SELECT g.id, g.name, g.description,
#         g.created_at, greatest(max(fw.updated_at), g.updated_at) as updated_at,
#         COALESCE ( json_agg( distinct jsonb_build_object( 'film_id', fw.id ) ) FILTER (WHERE fw.id is not null), '[]' ) as film_ids
#         FROM content.genre g
#         LEFT JOIN content.genre_film_work gfw ON gfw.genre_id = g.id
#         LEFT JOIN content.film_work fw ON fw.id = gfw.film_work_id
#         WHERE fw.updated_at >= %s OR g.updated_at >= %s
#         GROUP BY g.id
#         ORDER BY updated_at ASC
# """

sql_query_persons = """
        SELECT p.id, p.full_name, p.created_at, p.updated_at, 
        STRING_AGG(DISTINCT fw.id::text, ', ') as film_ids 
        FROM content.person p 
        LEFT JOIN content.person_film_work pfw ON pfw.person_id = p.id 
        LEFT JOIN content.film_work fw ON fw.id = pfw.film_work_id 
        WHERE p.updated_at >= %s 
        GROUP BY p.id 
        ORDER BY updated_at ASC;
"""

# sql_query_persons = """
#         SELECT p.id, p.full_name, p.created_at, greatest(max(fw.updated_at), p.updated_at) as updated_at,
#         COALESCE ( json_agg( distinct jsonb_build_object( 'film_id', fw.id ) ) FILTER (WHERE fw.id is not null), '[]' ) as film_ids
#         FROM content.person p
#         LEFT JOIN content.person_film_work pfw ON pfw.person_id = p.id
#         LEFT JOIN content.film_work fw ON fw.id = pfw.film_work_id
#         WHERE fw.updated_at >= %s OR p.updated_at >= %s
#         GROUP BY p.id
#         ORDER BY updated_at ASC
# """

STATE_KEY_MOVIES = 'last_movies_updated'  # ключ в словаре хранилища состояний. последний обновленный фильм
STATE_KEY_GENRES = 'last_genres_updated'  # ключ в словаре хранилища состояний. последний обновленный жанр
STATE_KEY_PERSONS = 'last_persons_updated'  # ключ в словаре хранилища состояний. последний обновленный жанр


def index_prep_movie(movie):
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
            "actors_names": [act['person_name'] for act in movie['persons'] if
                             act['person_role'] == 'actor' or act['person_role'] == 'AC'],
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


def index_prep_genre(genre_sql):
    """формирование индекса"""
    genre_dict_res = {
        "index": {"_index": "genres", "_id": str(genre_sql['id'])},
        "doc": {
            "id": str(genre_sql['id']),
            "name": genre_sql['name'],
            "description": genre_sql['description'],
            "created_at": genre_sql['created_at'],
            "film_ids": genre_sql['film_ids'].split(', ') #[act['film_id'] for act in genre_sql['film_ids']],
        },
        "updated_at": genre_sql['updated_at']
    }
    return genre_dict_res


def index_prep_person(person_sql):
    """формирование индекса"""
    person_dict_res = {
        "index": {"_index": "persons", "_id": str(person_sql['id'])},
        "doc": {
            "id": str(person_sql['id']),
            "full_name": person_sql['full_name'],
            "created_at": person_sql['created_at'],
            "film_ids": person_sql['film_ids'].split(', ') #[act['film_id'] for act in person_sql['film_ids']],
        },
        "updated_at": person_sql['updated_at']
    }
    return person_dict_res


####################################################################
# КОРУТИНЫ ФИЛЬМОВ
####################################################################
# этой корутине передаем курсор, который получаем из базы ОДИН раз.
# не тратим ресурсы на получение курсора каждый раз
@coroutine
def fetch_changed_movies(cur_movie, next_node_movies: Generator) -> Generator[datetime, None, None]:
    while last_updated := (yield):  # yield принимаем datetime
        # логгер
        logger.info(f'Fetching movies changed after ' f'{last_updated}')
        # выбираем все фильмы где updated_at больше значения %s
        # %s присылается из last_updated := (yield)
        # сортируем order by updated_at что бы в следующий раз брать самую свежую запись
        # sql = 'SELECT * FROM content.film_work WHERE updated_at > %s order by updated_at asc'
        # logger.info('Fetching movies updated after %s', last_updated)
        cur_movie.execute(query=sql_query_movies, params=(last_updated,))
        while results := cur_movie.fetchmany(size=100):  # передаем пачками
            next_node_movies.send(results)  # передаем следующую корутину


@coroutine
@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError))
def transform_movies(next_node_movies: Generator) -> Generator[list[dict], None, None]:
    # принимаем next_node корутину из предущего метода. Generator[list[dict] список из словарей
    while movie_dicts := (yield):
        batch = []
        for movie_dict in movie_dicts:  # итерируем СПИСОК из словарей
            movie_dict_prep = index_prep_movie(movie_dict)  # трансформация данных
            movie = Base_Model(**movie_dict_prep)  # инициализируем BaseModel Класс Movie cо словарем как аргументом
            batch.append(movie)  # подготовка списка из Объектов Movie
        next_node_movies.send(batch)  # передаем следующий Список из Словарей (объект Movie)


@coroutine
@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError))
def save_movies(state: State) -> Generator[list[Base_Model], None, None]:
    # загрузка документов в индексы в ElasticSearch
    # movies - Список из Словарей Объектов Base_Model
    while movies := (yield):
        body = []
        for movie in movies:
            index_dict = {'index': movie.index}
            body.append(index_dict)
            body.append(movie.doc)  #
        logger.info(f'ADDED, {type(body)=} {body=}')  # логируем JSON
        res = es.bulk(operations=body, )
        logger.info(res)
        print('**MOVIES**')
        print('Q-ty of Movies inserted=', len(movies), 'list of movies', [m.doc['title'] for m in movies])
        state.set_state(STATE_KEY_MOVIES,
                        str(movies[-1].updated_at))
        # сохраняем последний фильм из ранее отсортированного по order by updated_at в хранилище
        # если что-то упадет, то следующий раз начнем с этого фильма.


####################################################################
# КОРУТИНЫ ЖАНРОВ
####################################################################
# этой корутине передаем курсор, который получаем из базы ОДИН раз.
# не тратим ресурсы на получение курсора каждый раз
@coroutine
def fetch_changed_genres(cur_genre, next_node_genres: Generator) -> Generator[datetime, None, None]:
    while last_updated := (yield):  # yield принимаем datetime
        # логгер
        logger.info(f'Fetching genres changed after ' f'{last_updated}')
        # выбираем все жанры где updated_at больше значения %s
        # %s присылается из last_updated := (yield)
        cur_genre.execute(query=sql_query_genres, params=(last_updated,))
        # cursor.execute(sql_query_genres, (last_updated, last_updated, last_updated,))
        # while results := cursor.fetchmany(size=100):  # передаем пачками
        while results := cur_genre.fetchmany(size=100):  # передаем пачками
            next_node_genres.send(results)  # передаем следующую корутину


@coroutine
@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError))
def transform_genres(next_node_genres: Generator) -> Generator[list[dict], None, None]:
    # принимаем next_node корутину из предущего метода. Generator[list[dict] список из словарей
    while genre_dicts := (yield):
        batch = []
        for genre_dict in genre_dicts:  # итерируем СПИСОК из словарей
            genre_dict_prep = index_prep_genre(genre_dict)  # трансформация данных
            genre_model = Base_Model(
                **genre_dict_prep)  # инициализируем BaseModel Класс Movie cо словарем как аргументом
            batch.append(genre_model)  # подготовка списка из Объектов Movie
        next_node_genres.send(batch)  # передаем следующий Список из Словарей (объект Movie)


@coroutine
@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError))
def save_genres(state: State) -> Generator[list[Base_Model], None, None]:
    # загрузка документов в индексы в ElasticSearch
    while genre_dicts := (yield):
        body = []
        for genre_model in genre_dicts:
            index_dict = {'index': genre_model.index}
            body.append(index_dict)
            body.append(genre_model.doc)  #
        logger.info(f'ADDED, {type(body)=} {body=}')  # логируем JSON
        res = es.bulk(operations=body, )
        logger.info(res)
        print('**GENRES**')
        print('Q-ty of Genres inserted=', len(genre_dicts), 'list of genres', [g.doc['name'] for g in genre_dicts])
        state.set_state(STATE_KEY_GENRES, str(genre_dicts[-1].updated_at))
        # сохраняем последний фильм из ранее отсортированного по order by updated_at в хранилище
        # если что-то упадет, то следующий раз начнем с этого фильма.


####################################################################
# КОРУТИНЫ ПЕРСОН
####################################################################
# этой корутине передаем курсор, который получаем из базы ОДИН раз.
# не тратим ресурсы на получение курсора каждый раз
@coroutine
def fetch_changed_persons(cur_person, next_node_persons: Generator) -> Generator[datetime, None, None]:
    while last_updated := (yield):  # yield принимаем datetime
        # логгер
        logger.info(f'Fetching persons changed after ' f'{last_updated}')
        # выбираем все жанры где updated_at больше значения %s
        # %s присылается из last_updated := (yield)
        cur_person.execute(query=sql_query_persons, params=(last_updated,))
        while results := cur_person.fetchmany(size=100):  # передаем пачками
            next_node_persons.send(results)  # передаем следующую корутину


@coroutine
@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError))
def transform_persons(next_node_persons: Generator) -> Generator[list[dict], None, None]:
    # принимаем next_node корутину из предущего метода. Generator[list[dict] список из словарей
    while person_dicts := (yield):
        batch = []
        for person_dict in person_dicts:  # итерируем СПИСОК из словарей
            person_dict_prep = index_prep_person(person_dict)  # трансформация данных
            person_model = Base_Model(
                **person_dict_prep)  # инициализируем BaseModel Класс Movie cо словарем как аргументом
            batch.append(person_model)  # подготовка списка из Объектов Movie
        next_node_persons.send(batch)  # передаем следующий Список из Словарей (объект Movie)


@coroutine
@backoff.on_exception(backoff.expo,
                      (requests.exceptions.Timeout,
                       requests.exceptions.ConnectionError))
def save_persons(state: State) -> Generator[list[Base_Model], None, None]:
    # загрузка документов в индексы в ElasticSearch
    while person_dicts := (yield):
        body = []
        for person_model in person_dicts:
            index_dict = {'index': person_model.index}
            body.append(index_dict)
            body.append(person_model.doc)  #
        logger.info(f'ADDED, {type(body)=} {body=}')  # логируем JSON
        res = es.bulk(operations=body, )
        logger.info(res)
        print('**PERSONS**')
        print('Q-ty of Persons inserted=', len(person_dicts), 'list of person', [p.doc['full_name'] for p in person_dicts])
        state.set_state(STATE_KEY_PERSONS, str(person_dicts[-1].updated_at))
        # сохраняем последний фильм из ранее отсортированного по order by updated_at в хранилище
        # если что-то упадет, то следующий раз начнем с этого фильма.


if __name__ == '__main__':
    # start ElasticSearch

    # создание индексов в ElasticSearch
    es_index_json_file = {'movies': 'es_movies.json', 'genres': 'es_genres.json', 'persons': 'es_persons.json'}
    try:
        # перебор по 3м индексам и файлам из словаря es_index_json_file
        for index_name in es_index_json_file:
            es = Elasticsearch(os.getenv('ES_HOST_PORT'))
            # make Index ElasticSearch
            if not es.indices.exists(index=index_name):
                with open(es_index_json_file[index_name], 'r') as file:
                    data = json.load(file)
                    es.indices.create(index=index_name, body=data)
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

        # КОРУТИНЫ ФИЛЬМОВ
        saver_coro_movies = save_movies(state)  # сюда передаем последнее состояние state
        transformer_coro_movies = transform_movies(
            next_node_movies=saver_coro_movies)  # сюда передаем предыдущую корутину
        fetcher_coro_movies = fetch_changed_movies(cur,
                                                   next_node_movies=transformer_coro_movies)  # сюда передаем предыдущую корутину и курсор

        # КОРУТИНЫ ЖАНРОВ
        saver_coro_genres = save_genres(state)  # сюда передаем последнее состояние state
        transformer_coro_genres = transform_genres(
            next_node_genres=saver_coro_genres)  # сюда передаем предыдущую корутину
        fetcher_coro_genres = fetch_changed_genres(cur,
                                                   next_node_genres=transformer_coro_genres)  # сюда передаем предыдущую корутину и курсор

        # КОРУТИНЫ ПЕРСОН
        saver_coro_persons = save_persons(state)  # сюда передаем последнее состояние state
        transformer_coro_persons = transform_persons(
            next_node_persons=saver_coro_persons)  # сюда передаем предыдущую корутину
        fetcher_coro_persons = fetch_changed_persons(cur,
                                                     next_node_persons=transformer_coro_persons)  # сюда передаем предыдущую корутину и курсор

        while True:
            # КОРУТИНЫ ФИЛЬМОВ
            last_movies_updated = state.get_state(
                STATE_KEY_MOVIES)  # достаем (get_state) сохраненное состояние по ключу STATE_KEY_MOVIES
            logger.info('Starting ETL MOVIES process for updates ...')

            fetcher_coro_movies.send(
                state.get_state(STATE_KEY_MOVIES) or str(datetime.min))  # запускаем первую корутину ФИЛЬМОВ

            # КОРУТИНЫ ЖАНРОВ
            last_genres_updated = state.get_state(
                STATE_KEY_GENRES)  # достаем (get_state) сохраненное состояние по ключу STATE_KEY_GENRES
            logger.info('Starting ETL GENRES process for updates ...')

            fetcher_coro_genres.send(
                state.get_state(STATE_KEY_GENRES) or str(datetime.min))  # запускаем первую корутину ЖАНРОВ

            # КОРУТИНЫ ПЕРСОН
            last_persons_updated = state.get_state(
                STATE_KEY_PERSONS)  # достаем (get_state) сохраненное состояние по ключу STATE_KEY_PERSONS
            logger.info('Starting ETL PERSONS process for updates ...')

            fetcher_coro_persons.send(
                state.get_state(STATE_KEY_PERSONS) or str(datetime.min))  # запускаем первую корутину ПЕРСОН
            print('**TIME**')
            print('last date of updated movie', state.get_state(STATE_KEY_MOVIES))
            print('last date of updated genre', state.get_state(STATE_KEY_GENRES))
            print('last date of updated person', state.get_state(STATE_KEY_PERSONS))
            sleep(10)  # вечный цикл который ждет изменений в базе. С задержкой 10 сек

