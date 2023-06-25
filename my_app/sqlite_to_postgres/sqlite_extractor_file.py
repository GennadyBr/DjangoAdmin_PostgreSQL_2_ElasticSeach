from datetime import datetime
from config import step


class SQLiteExtractor:
    def __init__(self, sqlite_conn, db_name, logger) -> None:
        self.sqlite_conn = sqlite_conn
        self.db_name = db_name
        self.logger = logger

        self.sqlite_cursor = self.sqlite_conn.cursor()

    def extract_movies(self, offset) -> list:
        try:
            self.sqlite_cursor.execute(f"SELECT * FROM {self.db_name} LIMIT {step} OFFSET {offset};")
            data = self.sqlite_cursor.fetchall()  # оставил fetchall(), потому что ограничил выгрузку из БД через SELECT LIMIT
            self.logger.info(f'table SQLite.{self.db_name}, extracted {len(data)} rows')
            return data
        except Exception as exc:
            self.logger.error(exc)
