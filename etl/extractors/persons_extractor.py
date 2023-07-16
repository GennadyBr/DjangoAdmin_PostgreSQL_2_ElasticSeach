from datetime import datetime
from typing import Generator

from decorators import coroutine
from helpers.logger import logger

# этой корутине передаем курсор, который получаем из базы ОДИН раз.
# не тратим ресурсы на получение курсора каждый раз

@coroutine
def fetch_changed_persons(cur_person, next_node_persons: Generator) -> Generator[datetime, None, None]:
    sql_query_persons = """
            SELECT p.id, p.full_name, p.modified, 
            json_agg( distinct jsonb_build_object( 'film_id', pfw.film_work_id, 'role', pfw.role )) as film_ids 
            FROM content.person p 
            LEFT JOIN content.person_film_work pfw ON pfw.person_id = p.id 
            LEFT JOIN content.film_work fw ON fw.id = pfw.film_work_id 
            WHERE p.modified > %s 
            GROUP BY p.id 
            ORDER BY modified ASC;
    """

    while last_updated := (yield):  # yield принимаем datetime
        # логгер
        logger.info(f'Fetching PERSONS changed after ' f'{last_updated}')
        # выбираем все жанры где modified больше значения %s
        # %s присылается из last_updated := (yield)
        cur_person.execute(query=sql_query_persons, params=(last_updated,))
        while results := cur_person.fetchmany(size=100):  # передаем пачками
            next_node_persons.send(results)  # передаем следующую корутину
