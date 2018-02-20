import os
import pathlib
import pyarrow as pa
import numpy as np

from .config import config
from .schema import Schema
from .experiment_constants import *

class SerializedExperimentState(object):

    @staticmethod
    def initialize(experiment_uuid_hex):
        ex = SerializedExperimentState(experiment_uuid_hex)
        dimension = Schema.for_experiment(experiment_uuid_hex).dimension()

        ex._state.initialize(np.array([0.5, 0, 0]))
        ex.outcome_counts.initialize(np.zeros((4,), 'int64'))
        for variant in VARIANTS:
            ex.by_variant[variant][XX].initialize(np.zeros((dimension, dimension)))
            ex.by_variant[variant][XY].initialize(np.zeros((dimension,)))
            ex.by_variant[variant][MLE_WEIGHTS].initialize(np.zeros((dimension,)))
            ex.by_variant[variant][DISCRIMINITIVE_MASK].initialize(np.zeros((dimension,), dtype='int8'))

    def __init__(self, experiment_uuid_hex, variants=VARIANTS):
        self.eid = experiment_uuid_hex
        self.path = os.path.join(config.get('stats_base_dir'), str(self.eid))

        self.open = []

        # Fields
        self.outcome_counts = self._serialized('outcome_counts.dat')
        self.by_variant = {
            variant: {
                XX: self._serialized(variant, 'xx.dat'),
                XY: self._serialized(variant, 'yy.dat'),
                MLE_WEIGHTS: self._serialized(variant, 'mle_weights.dat'),
                DISCRIMINITIVE_MASK: self._serialized(variant, 'dm.dat'),
            }
            for variant in variants
        }
        self._state = self._serialized('sig_state.dat')
        (
            self.b_loss,
            self.significance,
            self.reached_significance
        ) = [FieldAccessor(self._state, i) for i in range(3)]

    def __enter__(self):
        self._open = {}
        return self

    def __exit__(self, *args):
        for mat in self.open:
            mat.persist()

    def _serialized(self, *path):
        *base_path, name = path
        base_path = os.path.join(self.path, *base_path)
        attr = SerializedMatrixAccessor(base_path, name)
        self.open.append(attr)
        return attr

class AccessorMixin(object):

    def incr(self, incr_by):
        self.set(self.get() + incr_by)

class FieldAccessor(AccessorMixin):

    def __init__(self, back, idx):
        self.back = back
        self.idx = idx

    def get(self):
        return self.back.get()[self.idx]

    def set(self, val):
        self.back.get()[self.idx] = val

class LazySerializedAccessor(AccessorMixin):

    def __init__(self, loader, serializer):
        self.value = None
        self.loader = loader
        self.serializer = serializer

    def get(self):
        if self.value is None:
            self.value = self.loader()
        return self.value

    def set(self, value):
        self.value = value

    def persist(self):
        self.serializer(self.value)

class SerializedMatrixAccessor(LazySerializedAccessor):

    def __init__(self, base_path, name):
        super().__init__(self._load, self._serialize)
        self.base_path = base_path
        self.name = name
        self.path = os.path.join(self.base_path, self.name)

    def initialize(self, init):
        pathlib.Path(self.base_path).mkdir(parents=True, exist_ok=True)
        with pa.OSFile(self.path, 'w') as outf:
            outf.write(pa.serialize(init).to_buffer())

    def _mutable_copy(self, matrix):
        mutable = np.ndarray(matrix.shape, dtype=matrix.dtype)
        mutable[:] = matrix[:]
        return mutable

    def _load(self):
        with pa.memory_map(self.path) as inf:
            mat = pa.deserialize(inf.read_buffer())
            return self._mutable_copy(mat)

    def _serialize(self, value):
        if value is not None:
            with pa.memory_map(self.path, 'w') as outf:
                outf.write(pa.serialize(value).to_buffer())
