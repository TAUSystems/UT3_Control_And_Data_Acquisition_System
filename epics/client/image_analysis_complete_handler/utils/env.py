from dotenv import dotenv_values
from os import environ

def get_env(dotenv=True, os=True) -> dict:
    """ Load environment variables from .env file and/or operating system
    
    Parameters
    ----------
    dotenv : bool
        whether to include environment variables from a .env file
    os : bool
        whether to include environment variables from the operating system
    """
    env = {}
    if dotenv:
        env.update(dotenv_values())
    if os:
        env.update(environ)

    return env
