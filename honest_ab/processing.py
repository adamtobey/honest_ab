import os
import numpy as np

from .config import config
from .redis import rd, rd_experiment_key
from .serialization import serialize_matrix, serialize_new_matrix, deserialize_matrix, experiment_path
from .schemas import process_json_blobs, get_experiment_schema, _data_dimension # TODO this sucks

# TODO tests

def initialize_processing_directory(experiment_uuid_hex, schema):
    dimension = _data_dimension(schema)

    path = experiment_path(experiment_uuid_hex)
    xx = np.zeros((dimension, dimension))
    xy = np.zeros((dimension,))

    for variant in ['a', 'b']: # TODO SPOT
        serialize_new_matrix(xx, path, variant, 'xx.dat')
        serialize_new_matrix(xy, path, variant, 'xy.dat')

def _pop_batch(experiment_uuid_hex):
    redis_key = rd_experiment_key(experiment_uuid_hex, 'wal')
    with rd.pipeline() as pipe:
        pipe.multi()
        pipe.lrange(redis_key, 0, config.get('batch_size') - 1)
        pipe.ltrim(redis_key, config.get('batch_size'), -1)
        batch = pipe.execute()[0]

    return batch

def process_batch(experiment_uuid_hex):
    json_batch = _pop_batch(experiment_uuid_hex)

    X, y, variant_boundary = process_json_blobs(experiment_uuid_hex, json_batch)

    # TODO too much implicit coupling across files through this format and magic strings
    y_a, y_b = y[:variant_boundary], y[variant_boundary:]
    batches = [
        ('a', X[:variant_boundary], y[:variant_boundary]),
        ('b', X[variant_boundary:], y[variant_boundary:])
    ]

    # Update significance model
    a_pos, b_pos = np.sum(y_a == 1), np.sum(y_b == 1)
    a_neg, b_neg = np.sum(y_a == 0), np.sum(y_b == 0)
    # TODO update the model

    # Update regression models
    regression_path = experiment_path(experiment_uuid_hex)
    for variant, X, y in batches:
        xx = deserialize_matrix(regression_path, variant, 'xx.dat')
        xy = deserialize_matrix(regression_path, variant, 'xy.dat')

        # TODO seems prone to overflows
        xx += X.T @ X
        xy += np.dot(X.T, y)

        serialize_matrix(xx, regression_path, variant, 'xx.dat')
        serialize_matrix(xy, regression_path, variant, 'xy.dat')
