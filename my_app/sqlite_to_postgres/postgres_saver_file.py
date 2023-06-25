import psycopg2

from psycopg2.extras import DictCursor
from dataclasses import fields, astuple

from data_classes_file import table_data_class_dict, Film_work_data_class, Person_data_class, Genre_data_class, \
    Genre_film_work_data_class, Person_film_work_data_class


class PostgresSaver():
    def __init__(self, pg_conn, db_name, logger) -> None:
        self.pg_conn = pg_conn
        self.cursor = pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        self.db_name = db_name
        self.logger = logger

    def insert_to_postgres(self, user) -> None:
        try:
            column_names = [field.name for field in fields(user)]
            # В зависимости от количества колонок генерируем под них %s.
            col_count = ', '.join(['%s'] * len(column_names))
            # формируем кортеж с данными для вставки
            bind_values = self.cursor.mogrify(f"({col_count})", astuple(user)).decode('utf-8')
            # # КОСТЫЛЬ заменяем 'movie' и 'tv_show' на 'MV' и 'TV' (для вставки в Filmwork)
            # bind_values.replace('movie', 'MV').replace('tv_show', 'TV')
            # формируем INSERT
            query = (
                f"""INSERT INTO content.{self.db_name} ({', '.join(column_names)}) VALUES {bind_values} ON CONFLICT (id) DO NOTHING""")
            try:
                #вставляем query в Postgres
                self.cursor.execute(query)
            except Exception as exc:
                self.logger.info(query)
                self.logger.error(exc)
            self.pg_conn.commit()
        except Exception as exc:
            self.logger.error(exc)
            self.pg_conn.rollback()

    def save_all_data(self, data) -> None:
        # загрузка данных по ОДНОЙ строке
        try:
            for i in data:
                if self.db_name in table_data_class_dict:
                    user = eval(table_data_class_dict[self.db_name])(**dict(i))
                    PostgresSaver.insert_to_postgres(self, user)
                else:
                    self.logger.info(user)
                    raise Exception

            self.logger.info(f'table Postgres.{self.db_name}. inserted {len(data)} rows')


        except Exception as exc:
            self.logger.error(exc)
            self.pg_conn.rollback()
