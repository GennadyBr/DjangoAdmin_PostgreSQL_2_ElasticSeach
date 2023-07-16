from typing import Generator

import backoff
import requests

from decorators import coroutine
from jsons.models_state import Base_Model


def index_prep_genre(genre_sql):
    """формирование индекса"""
    genre_dict_res = {
        "index": {"_index": "genres", "_id": str(genre_sql['id'])},
        "doc": {
            "id": str(genre_sql['id']),
            "name": genre_sql['name'],
            "description": genre_sql['description'],
            "film_ids": genre_sql['film_ids'].split(', ')  # [act['film_id'] for act in genre_sql['film_ids']],
        },
        "modified": genre_sql['modified']
    }
    return genre_dict_res


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
