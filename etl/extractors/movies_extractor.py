from datetime import datetime
from typing import Generator

from decorators import coroutine
from helpers.logger import logger
# этой корутине передаем курсор, который получаем из базы ОДИН раз.
# не тратим ресурсы на получение курсора каждый раз


@coroutine
def fetch_changed_movies(cur_movie, next_node_movies: Generator) -> Generator[datetime, None, None]:
    sql_query_movies = """
            SELECT fw.id, fw.title, fw.description, fw.rating, fw.type,
            fw.created, greatest(fw.modified, max(p.modified), max(g.modified)) as modified, 
            COALESCE ( json_agg( distinct jsonb_build_object( 'person_role', pfw.role, 'person_id', p.id, 
            'person_name', p.full_name ) ) FILTER (WHERE p.id is not null), '[]' ) as persons, 
            array_agg(DISTINCT g.name) as genres 
            FROM content.film_work fw 
            LEFT JOIN content.person_film_work pfw ON pfw.film_work_id = fw.id 
            LEFT JOIN content.person p ON p.id = pfw.person_id 
            LEFT JOIN content.genre_film_work gfw ON gfw.film_work_id = fw.id 
            LEFT JOIN content.genre g ON g.id = gfw.genre_id 
            WHERE fw.modified > %s or p.modified > %s or g.modified > %s
            GROUP BY fw.id 
            ORDER BY modified ASC
    """
    while last_updated := (yield):  # yield принимаем datetime
        # логгер
        logger.info(f'Fetching MOVIES changed after ' f'{last_updated}')
        # выбираем все фильмы где modified больше значения %s
        # %s присылается из last_updated := (yield)
        # сортируем order by modified что бы в следующий раз брать самую свежую запись
        cur_movie.execute(query=sql_query_movies, params=(last_updated, last_updated, last_updated,))
        while results := cur_movie.fetchmany(size=100):  # передаем пачками
            next_node_movies.send(results)  # передаем следующую корутину
