from typing import Generator

import backoff
import requests

from decorators import coroutine
from jsons.models_state import Base_Model


def index_prep_person(person_sql):
    """формирование индекса"""
    person_dict_res = {
        "index": {"_index": "persons", "_id": str(person_sql['id'])},
        "doc": {
            "id": str(person_sql['id']),
            "full_name": person_sql['full_name'],
            "films": person_sql['film_ids']  # .split(', ')  # [act['film_id'] for act in person_sql['film_ids']],
        },
        "modified": person_sql['modified']
    }
    return person_dict_res


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
