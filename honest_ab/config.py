import os
import re
from flask.config import Config

def apply_redis(config):
    redis_url = os.environ.get('REDIS_URL', False)
    if redis_url:
        p, u, pwd_host, port = redis_url.split(":")
        pwd, host = pwd_host.split('@')
        config.update(dict(
            redis_host=host,
            redis_port=int(port),
            redis_pwd=pwd
        ))

def apply_db(config):
    db_url = os.environ.get('DATABASE_URL', False)
    if db_url:
        p, ss_user, pwd_host, port_db = db_url.split(":")
        pwd, host = pwd_host.split('@')
        port, db = port_db.split("/")
        user = ss_user[2:]
        config.update(dict(
            db_host=host,
            db_port=int(port),
            db_user=user,
            db_password=pwd,
            db_name=db
        ))


config = Config(root_path=os.path.abspath('.'))
config.update(dict(
    testing=False,

    redis_host='localhost',
    redis_port=6379,
    redis_pwd=None,
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

apply_redis(config)
apply_db(config)
