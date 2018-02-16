import redis

from .config import config

# TODO config
rd = redis.StrictRedis(host=config.get('redis_host'), port=config.get('redis_port'), db=config.get('redis_db'))

def rd_experiment_key(experiment_uuid_hex, key):
    return f"{experiment_uuid_hex}:{key}"
