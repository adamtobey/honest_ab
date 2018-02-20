from .redis import rd, rd_experiment_key
from .compute import pp
from .batch_processor import BatchStatisticsProcessor
from .experiment_constants import VARIANTS, RESULTS
from .config import config

class InvalidTestSpecError(RuntimeError):
    pass

def _trigger_flush(experiment_uuid_hex):
    processor = BatchStatisticsProcessor(experiment_uuid_hex)
    pp.submit(processor.process)

def write_data_point_json(experiment_uuid_hex, variant, result, data_point_json):
    str_opts = lambda opts: " or ".join([f"'{opt}'" for opt in opts])
    if variant not in VARIANTS:
        raise InvalidTestSpecError(f"Variant must be either {str_opts(VARIANTS)}")
    if result not in RESULTS:
        raise InvalidTestSpecError(f"Result must be either {str_opts(RESULTS)}")

    redis_key = rd_experiment_key(experiment_uuid_hex, 'wal')

    log_size = rd.lpush(redis_key, data_point_json)
    if log_size % config.get('batch_size') == 0:
        _trigger_flush(experiment_uuid_hex)
