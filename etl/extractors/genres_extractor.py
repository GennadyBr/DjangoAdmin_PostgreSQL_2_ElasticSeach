from datetime import datetime
from typing import Generator

from decorators import coroutine
from helpers.logger import logger

# этой корутине передаем курсор, который получаем из базы ОДИН раз.
# не тратим ресурсы на получение курсора каждый раз

@coroutine
def fetch_changed_genres(cur_genre, next_node_genres: Generator) -> Generator[datetime, None, None]:
    sql_query_genres = """
            SELECT g.id, g.name, g.description, g.modified, 
            STRING_AGG(DISTINCT fw.id::text, ', ') as film_ids 
            FROM content.genre g 
            LEFT JOIN content.genre_film_work gfw ON gfw.genre_id = g.id 
            LEFT JOIN content.film_work fw ON fw.id = gfw.film_work_id 
            WHERE g.modified > %s 
            GROUP BY g.id 
            ORDER BY modified ASC;
    """

    while last_updated := (yield):  # yield принимаем datetime
        # логгер
        logger.info(f'Fetching GENRES changed after ' f'{last_updated}')
        # выбираем все жанры где modified больше значения %s
        # %s присылается из last_updated := (yield)
        cur_genre.execute(query=sql_query_genres, params=(last_updated,))
        # cursor.execute(sql_query_genres, (last_updated, last_updated, last_updated,))
        # while results := cursor.fetchmany(size=100):  # передаем пачками
        while results := cur_genre.fetchmany(size=100):  # передаем пачками
            next_node_genres.send(results)  # передаем следующую корутину
