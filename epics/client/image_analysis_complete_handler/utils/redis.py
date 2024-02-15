from redis import Redis
from os import environ as env

def get_redis_client():
    
    REDIS_HOST = env['IMAGE_BACKEND_REDIS_HOST']
    REDIS_PORT = env['IMAGE_BACKEND_REDIS_PORT']
    REDIS_PASSWORD = env['IMAGE_BACKEND_REDIS_PASSWORD']

    return Redis(REDIS_HOST, REDIS_PORT, password=REDIS_PASSWORD)
