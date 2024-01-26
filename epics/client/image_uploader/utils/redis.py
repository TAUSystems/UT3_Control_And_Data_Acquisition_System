from redis import Redis
from dotenv import dotenv_values

def get_redis_client():
    
    env = dotenv_values()

    REDIS_HOST = env['REDIS_HOST']
    REDIS_PORT = env['REDIS_PORT']
    REDIS_PASSWORD = env['REDIS_PASSWORD']

    return Redis(REDIS_HOST, REDIS_PORT, password=REDIS_PASSWORD)
