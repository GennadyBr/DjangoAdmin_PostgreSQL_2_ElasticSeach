import os

host = os.environ.get('DB_HOST', 'postgres_dc')
port = int(os.environ.get('DB_PORT', 5432))
db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('POSTGRES_USER')
db_pass = os.environ.get('POSTGRES_PASSWORD')

dsl = {'dbname': db_name, 'user': db_user, 'password': db_pass, 'host': host, 'port': port}
db_path = 'db.sqlite'
step = 3000 # количество единовременной выгрузки для SELECT LIMIT

