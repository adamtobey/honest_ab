import redis

from .config import config

rd = redis.StrictRedis(host='ec2-35-170-155-174.compute-1.amazonaws.com', port=12549, db=config.get('redis_db'), password='p40699dc4d03f4da2f15c70ff2bd804e5a8b22367962758c1b97e3b77fbd16e81')

def rd_experiment_key(experiment_uuid_hex, key):
    return f"{experiment_uuid_hex}:{key}"
