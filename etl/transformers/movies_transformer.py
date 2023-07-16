from typing import Generator

import backoff
import requests

from decorators import coroutine
from jsons.models_state import Base_Model


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
        "modified": movie['modified']
    }
    return movie_dict_res


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
