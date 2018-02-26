import redis

from .config import config

rd = redis.StrictRedis(
    host=config.get('redis_host'),
    port=config.get('redis_port'),
    db=0,
    password=config.get('redis_pwd')
)

def rd_experiment_key(experiment_uuid_hex, key):
    return f"{experiment_uuid_hex}:{key}"
