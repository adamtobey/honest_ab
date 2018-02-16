import os
import pathlib
import pyarrow as pa
import numpy as np

from .config import config

def experiment_path(experiment_uuid_hex):
    return os.path.join(config.get('stats_base_dir'), str(experiment_uuid_hex))

def _mutable_copy(matrix):
    mutable = np.ndarray(matrix.shape, dtype=matrix.dtype)
    mutable[:] = matrix[:]
    return mutable

def deserialize_matrix(*path, mutable=True):
    path = os.path.join(*path)
    with pa.memory_map(path) as inf:
        mat = pa.deserialize(inf.read_buffer())
        if mutable:
            return _mutable_copy(mat)
        else:
            return mat

def serialize_matrix(matrix, *path):
    path = os.path.join(*path)
    with pa.memory_map(path, 'w') as outf:
        outf.write(pa.serialize(matrix).to_buffer())

def serialize_new_matrix(matrix, *path, mkdir=True):
    if mkdir:
        pathlib.Path(os.path.join(*path[:-1])).mkdir(parents=True, exist_ok=True)
    path = os.path.join(*path)
    with pa.OSFile(path, 'w') as outf:
        outf.write(pa.serialize(matrix).to_buffer())
