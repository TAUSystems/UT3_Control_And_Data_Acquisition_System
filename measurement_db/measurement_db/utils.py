from __future__ import annotations

from sqlalchemy import create_engine, URL
from dotenv import dotenv_values
env = dotenv_values()

def get_sqlalchemy_engine():
    return create_engine(URL.create(env['MEASUREMENT_DB_SQLALCHEMY_DRIVER'],
                            host=env['MEASUREMENT_DB_HOST'],
                            port=env['MEASUREMENT_DB_PORT'],  
                            database=env['MEASUREMENT_DB_DBNAME'],
                            username=env['MEASUREMENT_DB_USERNAME'],
                            password=env['MEASUREMENT_DB_PASSWORD'],
                        ))

