from .redis import rd, rd_experiment_key
from .compute import pp
from .processing import process_batch
from .config import config
from pdb import set_trace

class InvalidTestSpecError(RuntimeError):
    pass

def _trigger_flush(experiment_uuid_hex):
    pp.submit(process_batch, experiment_uuid_hex=experiment_uuid_hex)

def write_data_point_json(experiment_uuid_hex, variant, result, data_point_json):
    if variant not in ["a", "b"]:
        raise InvalidTestSpecError("Variant must be either 'a' or 'b'")
    if result not in ["success", "failure"]:
        raise InvalidTestSpecError("Result must be either 'success' or 'failure'")

    redis_key = rd_experiment_key(experiment_uuid_hex, 'wal')

    log_size = rd.lpush(redis_key, data_point_json)
    if log_size % config.get('batch_size') == 0:
        _trigger_flush(experiment_uuid_hex)
