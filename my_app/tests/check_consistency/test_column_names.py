import sqlite3
import psycopg2
import logging

from contextlib import contextmanager
from psycopg2.extras import DictCursor

from .logging_config import init_logger
from .test_config import dsl, db_path, db_name_list


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


def test_column_names():
    """сравнение названия полей в таблицах Postgres и SQLite"""
    with open_sqlite3() as sqlite_conn, open_pg() as pg_conn:  #
        pg_cursor = pg_conn.cursor()
        sqlite_conn.row_factory = sqlite3.Row
        sqlite_cursor = sqlite_conn.cursor()

        for db_name in db_name_list:
            sqlite_cursor.execute(f"SELECT * FROM {db_name};")
            pg_cursor.execute(f"SELECT * FROM content.{db_name};")

            pg_col_names = [cn[0] for cn in pg_cursor.description]
            pg_col_names.sort(key=len)
            sqlite_col_names = [cn[0] for cn in sqlite_cursor.description]
            sqlite_col_names.sort(key=len)

            logger.info(f'Postgres.{db_name=} test_column_names {pg_col_names}')
            logger.info(f'SQLite.{db_name=} test_column_names {sqlite_col_names}')

            assert pg_col_names == sqlite_col_names


init_logger('my_app')
logger = logging.getLogger('my_app.test_column_names')

try:
    test_column_names()
except Exception as exc:
    logger.error(exc)
