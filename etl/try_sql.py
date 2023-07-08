import psycopg
from psycopg import ServerCursor
from psycopg.conninfo import make_conninfo
from psycopg.rows import dict_row

from etl.settings import database_settings

sql_query_genres = """
        SELECT g.id, g.name, g.description,
        g.created_at, greatest(max(fw.updated_at), g.updated_at) as updated_at, 
        COALESCE ( json_agg( distinct jsonb_build_object( 'film_id', fw.id ) ) FILTER (WHERE fw.id is not null), '[]' ) as film_ids 
        FROM content.genre g 
        LEFT JOIN content.genre_film_work gfw ON gfw.genre_id = g.id 
        LEFT JOIN content.film_work fw ON fw.id = gfw.genre_id 
        WHERE fw.updated_at >= %s OR g.updated_at >= %s
        GROUP BY g.id 
        ORDER BY updated_at ASC
"""
last_updated = "1000-06-16 23:14:09.514476+03:00"
dsl = {'dbname': 'movies_database', 'user': 'app', 'password': '123qwe', 'host': '127.0.0.1', 'port': 5432}

with psycopg.connect(**dsl, row_factory=dict_row) as conn, ServerCursor(conn, 'fetcher') as cur_genre:
    cur_genre.execute(query=sql_query_genres, params=(last_updated, last_updated,))

while results := cur_genre.fetchall():  # передаем пачками
    print('*G-FETCH*' * 10)
    print('result', results)
