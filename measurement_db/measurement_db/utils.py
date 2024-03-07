from __future__ import annotations

from sqlalchemy import create_engine, URL
from dotenv import dotenv_values
env = dotenv_values()

def get_sqlalchemy_engine():
    return create_engine(URL.create(env.get('MEASUREMENT_DB_SQLALCHEMY_DRIVER'),
                            host=env.get('MEASUREMENT_DB_HOST'),
                            port=env.get('MEASUREMENT_DB_PORT'),  
                            database=env.get('MEASUREMENT_DB_DBNAME'),
                            username=env.get('MEASUREMENT_DB_USERNAME'),
                            password=env.get('MEASUREMENT_DB_PASSWORD'),
                        ))

