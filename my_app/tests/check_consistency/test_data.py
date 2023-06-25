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


def test_data():
    """сравнение данных в Postgres и SQLite"""

    with open_sqlite3() as sqlite_conn, open_pg() as pg_conn:  #
        pg_cursor = pg_conn.cursor()
        sqlite_cursor = sqlite_conn.cursor()

        for db_name in db_name_list:
            sqlite_cursor.execute(f"SELECT * FROM {db_name};")
            pg_cursor.execute(f"SELECT * FROM content.{db_name};")

            sqlite_data = [str(i) for i in sqlite_cursor.fetchone()]
            pg_data = [str(i) for i in pg_cursor.fetchone()]

            assert len(sqlite_data) == len(pg_data)


init_logger('my_app')
logger = logging.getLogger('my_app.test_data')

try:
    test_data()
except Exception as exc:
    logger.error(exc)
