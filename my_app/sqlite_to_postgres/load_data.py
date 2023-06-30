import sqlite3
import psycopg2
import logging

from contextlib import contextmanager
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor

from postgres_saver_file import PostgresSaver
from sqlite_extractor_file import SQLiteExtractor
from config import dsl, db_path, step
from logging_config import init_logger


@contextmanager
def open_sqlite3():
    sqlite_conn = sqlite3.connect(db_path)
    try:
        logger.info("Creating connection sqlite_conn")
        yield sqlite_conn  # получение курсора conn.cursor()
    finally:
        logger.info("Closing connection sqlite_conn")
        sqlite_conn.close()


@contextmanager
def open_pg():
    pg_conn = psycopg2.connect(**dsl, cursor_factory=DictCursor)
    try:
        logger.info("Creating connection pg_conn")
        yield pg_conn  # получение курсора conn.cursor()
    finally:
        logger.info("Closing connection pg_conn")
        pg_conn.close()


def main():
    with open_sqlite3() as sqlite_conn, open_pg() as pg_conn:
        # По-умолчанию SQLite возвращает строки в виде кортежа значений. Эта строка указывает, что данные должны быть в формате «ключ-значение»
        sqlite_conn.row_factory = sqlite3.Row
        pg_cursor = pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)  # получение курсора
        sqlite_cursor = sqlite_conn.cursor()  # получение курсора

        #по просьбе ревьюра добавлено сюда миграция
        # call_command("migrate", interactive=False)
        # call_command("collectstatic - -noinput", interactive=False)

        db_name_list_sql = sqlite_cursor.execute(
            f"SELECT * FROM sqlite_master WHERE type='table';")  # получение объекта писка таблиц
        # формирование списка таблиц
        db_name_list_obj = []
        db_name_list_obj = [i for i in db_name_list_sql.fetchall()]
        db_name_list = []
        db_name_list = [i[1] for i in db_name_list_obj]
        db_name_list.sort(key=len)
        # цикл перебора БД
        for db_name in db_name_list:
            logger.info(f'start handling {db_name=}')
            pg_cursor.execute(f"""TRUNCATE content.{db_name} CASCADE""")  # удаление содержимого БД
            load_from_sqlite(sqlite_conn, pg_conn, db_name)


def load_from_sqlite(sqlite_conn: sqlite3.Connection, pg_conn: _connection, db_name: str) -> None:

    """Основной метод загрузки данных из SQLite в Postgres"""
    postgres_saver = PostgresSaver(pg_conn, db_name, logger)  # инициализация экземпляра класса PostgresSaver

    sqlite_conn.row_factory = sqlite3.Row
    sqlite_extractor = SQLiteExtractor(sqlite_conn, db_name, logger)  # инициализация экземпляра класса SQLiteExtractor



    # цикл извлечения и записи данных по пачкам с шагом (step)
    offset = 0
    while True:
        data = sqlite_extractor.extract_movies(offset)  # получение данных из SQLite
        if not data:
            logger.info(f'finish handling {db_name=}')
            break
        postgres_saver.save_all_data(data)  # запись данных в Postrges
        offset += step


if __name__ == '__main__':
    init_logger('my_app')
    logger = logging.getLogger('my_app.load_data')

    main()
