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


def test_rows_num_sqlite_postgres():
    """сравнение количества записей в таблицах Postgres SQLite"""

    with open_sqlite3() as sqlite_conn, open_pg() as pg_conn:  #
        pg_cursor = pg_conn.cursor()
        sqlite_cursor = sqlite_conn.cursor()

        for db_name in db_name_list:
            sqlite_query = f"SELECT * FROM {db_name};"
            pg_query = f"SELECT * FROM content.{db_name};"

            sqlite_cursor.execute(sqlite_query)
            sqlite_data = sqlite_cursor.fetchall()

            pg_cursor.execute(pg_query)
            pg_data = pg_cursor.fetchall()
            logger.info(f'Postgres.{db_name=} number of row {len(pg_data)}')
            logger.info(f'SQLite.{db_name=} number of row {len(sqlite_data)}')

            assert len(pg_data) == len(sqlite_data)


init_logger('my_app')
logger = logging.getLogger('my_app.test_row_numbers')

try:
    test_rows_num_sqlite_postgres()
except Exception as exc:
    logger.error(exc)
