import abc
import json
import uuid
import zoneinfo
from typing import Any
from datetime import datetime, date
from pydantic import BaseModel, root_validator

from json import JSONDecodeError
from logging import Logger
from typing import Optional


class BaseStorage:
    @abc.abstractmethod
    def save_state(self, state: dict) -> None:
        ...

    @abc.abstractmethod
    def retrieve_state(self) -> dict:
        ...


class JsonFileStorage(BaseStorage):
    def __init__(
            self, logger: Logger, file_path: Optional[str] = 'storage.json'
    ):
        self._logger = logger
        self.file_path = file_path

    def save_state(self, state: dict) -> None:
        """outfile - файл вывода"""
        with open(self.file_path, 'w') as outfile:
            json.dump(state, outfile)

    def retrieve_state(self) -> dict:
        """json_file - файл ввода"""
        try:
            with open(self.file_path, 'r') as json_file:
                return json.load(json_file)
        except (FileNotFoundError, JSONDecodeError):
            self._logger.warning(
                'No state file provided. Continue with default file'
            )
            return dict()


class State:
    """класс для хранения состояния в случае сбоя чего-либо.
    вызывается после ...
    """

    def __init__(self, storage: BaseStorage):
        self.storage = storage  # main.py init of instance of state = State(JsonFileStorage(logger=logger))
        # storage - экземпляр класса JsonFileStorage

    def set_state(self, key: str, value: Any) -> None:
        try:
            state = self.storage.retrieve_state()
        except FileNotFoundError:
            state = dict()
        state[key] = value
        self.storage.save_state(state)

    def get_state(self, key: str) -> Any:
        return self.storage.retrieve_state().get(key)


class Movie(BaseModel):
    """
    Класс
    # BaseModel позволяет преобразовывать в JSON
    """
    index: Optional[dict] = {}
    doc: Optional[dict] = {}
    updated_at: datetime
