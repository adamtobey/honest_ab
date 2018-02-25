import os
from flask.config import Config

def _collect(schema):
    collected = {}
    for out_key, in_key in schema.items():
        value = os.environ.get(in_key, False)
        if value:
            collected[out_key] = value
    return collected


config = Config(root_path=os.path.abspath('.'))
config.update(dict(
    testing=False,

    redis_host='localhost',
    redis_port=6379,
    redis_db=0,

    db_host='localhost',
    db_name='honest-ab_development',
    db_user='honest-ab',
    db_password='honest-ab',
    db_port=5432,

    login_manager_secret_key='lakjsdlfkjasdlfkjasd',

    batch_size=30,

    stats_base_dir=os.path.abspath(os.path.join('.', 'stats'))
))

env = _collect(dict(
    db_host='RDS_HOSTNAME',
    db_port='RDS_PORT',
    db_name='RDS_DB_NAME',
    db_user='RDS_USERNAME',
    db_password='RDS_PASSWORD',
    login_manager_secret_key='LOGIN_KEY',
    redis_host='REDIS_HOST',
    redis_port='REDIS_PORT'
))
config.update(env)
