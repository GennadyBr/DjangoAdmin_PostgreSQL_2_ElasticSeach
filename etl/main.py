import os
import json
from typing import Generator

import backoff
import psycopg

from time import sleep
from datetime import datetime

import requests
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from psycopg import ServerCursor
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

from decorators import coroutine
from helpers.logger import logger
from settings import database_settings
from jsons.models_state import JsonFileStorage, State, Base_Model
from extractors.genres_extractor import fetch_changed_genres
from extractors.movies_extractor import fetch_changed_movies
from extractors.persons_extractor import fetch_changed_persons
from transformers.genres_transformer import transform_genres
from transformers.movies_transformer import transform_movies
from transformers.persons_transformer import transform_persons

load_dotenv()

STATE_KEY_MOVIES = 'last_movies_updated'  # ключ в словаре хранилища состояний. последний обновленный фильм
STATE_KEY_GENRES = 'last_genres_updated'  # ключ в словаре хранилища состояний. последний обновленный жанр
STATE_KEY_PERSONS = 'last_persons_updated'  # ключ в словаре хранилища состояний. последний обновленный жанр


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
        # logger.info(f'ADDED, {type(body)=} {body=}')  # логируем JSON
        res = es.bulk(operations=body, )
        # logger.info(res)
        logger.info('**GENRES**')
        logger.info(f'Q-ty of Genres inserted= {len(genre_dicts)}')
        logger.info(f'List of genres: {[g.doc["name"] for g in genre_dicts]}')
        state.set_state(STATE_KEY_GENRES, str(genre_dicts[-1].modified))
        # сохраняем последний фильм из ранее отсортированного по order by modified в хранилище
        # если что-то упадет, то следующий раз начнем с этого фильма.


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
        # logger.info(f'ADDED, {type(body)=} {body=}')  # логируем JSON
        res = es.bulk(operations=body, )
        # logger.info(res)
        logger.info('**MOVIES**')
        logger.info(f'Q-ty of Movies inserted= {len(movies)}')
        logger.info(f'List of movies {[m.doc["title"] for m in movies]}')
        state.set_state(STATE_KEY_MOVIES,
                        str(movies[-1].modified))
        # сохраняем последний фильм из ранее отсортированного по order by modified в хранилище
        # если что-то упадет, то следующий раз начнем с этого фильма.


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
        # logger.info(f'ADDED, {type(body)=} {body=}')  # логируем JSON
        res = es.bulk(operations=body, )
        # logger.info(res)
        logger.info('**PERSONS**')
        logger.info(f'Q-ty of Persons inserted= {len(person_dicts)}')
        logger.info(f'List of genres: {[g.doc["full_name"] for g in person_dicts]}')
        state.set_state(STATE_KEY_PERSONS, str(person_dicts[-1].modified))
        # сохраняем последний фильм из ранее отсортированного по order by modified в хранилище
        # если что-то упадет, то следующий раз начнем с этого фильма.


if __name__ == '__main__':
    # start ElasticSearch

    # создание индексов в ElasticSearch
    es_index_json_file = {'movies': 'es_movies.json', 'genres': 'es_genres.json', 'persons': 'es_persons.json'}
    try:
        # перебор по 3м индексам и файлам из словаря es_index_json_file
        for index_name in es_index_json_file:
            es = Elasticsearch(os.getenv('ES_HOST_PORT'))
            # waiting for ElasticSearch Ping
            while True:
                if es.ping():
                    break
                print('*****waiting for ElasticSearch Ping*****')
                sleep(1)

            # make Index ElasticSearch
            if not es.indices.exists(index=index_name):
                with open(es_index_json_file[index_name], 'r') as file:
                    data = json.load(file)
                    es.indices.create(index=index_name, body=data)
    except Exception as error:
        logger.info(
            f'{error=}, {es.info=}, {es.graph=}, {es.health_report=}, {es.logstash=}, {es.watcher=}, {es.transport=}, {es.__doc__=}')

    logger.info('Start loading data to Elasticsearch')
    storage = JsonFileStorage(logger, 'jsons/storage.json')
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
            logger.info('**TIME**')
            logger.info(f'last date of updated movie, {state.get_state(STATE_KEY_MOVIES)}')
            logger.info(f'last date of updated genre, {state.get_state(STATE_KEY_GENRES)}')
            logger.info(f'last date of updated person, {state.get_state(STATE_KEY_PERSONS)}')
            sleep(10)  # вечный цикл который ждет изменений в базе. С задержкой 10 сек
