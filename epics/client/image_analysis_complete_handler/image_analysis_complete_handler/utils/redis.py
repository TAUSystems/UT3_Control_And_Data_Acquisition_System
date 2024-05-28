from redis import Redis
from os import environ as env

def get_redis_client(**additional_redis_kwargs) -> Redis:
    """
    Host, port, username, and password are read from the OS environment, and 
    additional parameters may be passed in.
    """


    REDIS_HOST = env['IMAGE_BACKEND_REDIS_HOST']
    REDIS_PORT = env['IMAGE_BACKEND_REDIS_PORT']
    REDIS_USERNAME = env['IMAGE_BACKEND_REDIS_USERNAME']
    REDIS_PASSWORD = env['IMAGE_BACKEND_REDIS_PASSWORD']

    return Redis(REDIS_HOST, REDIS_PORT, username=REDIS_USERNAME, password=REDIS_PASSWORD, **additional_redis_kwargs)
