import os
from flask.config import Config

config = Config(root_path=os.path.abspath('.'))
config.update(dict(
    testing=False,

    redis_host='localhost',
    redis_port=6379,
    redis_db=0,

    batch_size=480,

    stats_base_dir=os.path.abspath(os.path.join('.', 'stats'))
))
