import datetime

from uuid import uuid4

from dataclasses import dataclass


@dataclass
class UU_ID_Mixin:
    id: uuid4


@dataclass
class Created_At_Mixin:
    created_at: datetime


@dataclass
class Updated_At_Mixin:
    updated_at: datetime


@dataclass
class Film_work_data_class(UU_ID_Mixin, Created_At_Mixin, Updated_At_Mixin):
    title: str
    description: str
    creation_date: datetime
    file_path: str
    rating: float
    type: str


@dataclass
class Person_data_class(UU_ID_Mixin, Created_At_Mixin, Updated_At_Mixin):
    full_name: str


@dataclass
class Genre_data_class(UU_ID_Mixin, Created_At_Mixin, Updated_At_Mixin):
    name: str
    description: str


@dataclass
class Genre_film_work_data_class(UU_ID_Mixin, Created_At_Mixin):
    genre_id: uuid4
    film_work_id: uuid4


@dataclass
class Person_film_work_data_class(UU_ID_Mixin, Created_At_Mixin):
    film_work_id: uuid4
    person_id: uuid4
    role: str


table_data_class_dict = {'film_work': 'Film_work_data_class', 'person': 'Person_data_class',
                         'genre': 'Genre_data_class', 'genre_film_work': 'Genre_film_work_data_class',
                         'person_film_work': 'Person_film_work_data_class'}
