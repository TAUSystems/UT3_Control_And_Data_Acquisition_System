from __future__ import annotations

from sqlalchemy import create_engine as create_sync_engine
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import URL

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy import Engine
    from sqlalchemy.ext.asyncio import AsyncEngine

from dotenv import dotenv_values
env = dotenv_values()

def get_sqlalchemy_engine(async_: bool = False) -> Engine | AsyncEngine:
    create_engine_ = create_async_engine if async_ else create_sync_engine

    if sqlalchemy_url := env.get('MEASUREMENT_DB_SQLALCHEMY_URL'):
        return create_engine_(sqlalchemy_url)
    
    else:
        return create_engine_(URL.create(env.get('MEASUREMENT_DB_SQLALCHEMY_DRIVER'),
                                host=env.get('MEASUREMENT_DB_HOST'),
                                port=env.get('MEASUREMENT_DB_PORT'),  
                                database=env.get('MEASUREMENT_DB_DBNAME'),
                                username=env.get('MEASUREMENT_DB_USERNAME'),
                                password=env.get('MEASUREMENT_DB_PASSWORD'),
                            ))

