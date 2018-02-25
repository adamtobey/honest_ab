import os
import pathlib
import pyarrow as pa
import numpy as np

from .config import config
from .schema import Schema
from .experiment_constants import *

class SerializedState(object):

    def __init__(self):
        self._fields = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.persist()

    def persist(self):
        for field in self._fields:
            field.persist()

    def _field(self, field):
        try:
            self._fields.append(field)
        except AttributeError:
            "All children of SerializedState must call its constructor"
        return field

    def _serialized(self, *path):
        *base_path, name = path
        base_path = os.path.join(self.path, *base_path)
        attr = SerializedMatrixAccessor(base_path, name)
        return self._field(attr)

class StreamingAverage(SerializedState):

    def initialize(self, shape):
        self._state.initialize(np.array([0, -1]))
        self.log.initialize(np.zeros(shape))
        self.accumulator.initialize(np.zeros(shape))

    def __init__(self, base_path, name):
        super().__init__()

        self.path = os.path.join(base_path, name)

        self._state = self._serialized('state.dat')
        self.log_size, self.acc_power = [FieldAccessor(self._state, i) for i in range(2)]
        self.log = self._serialized('log.dat')
        self.accumulator = self._serialized('accumulator.dat')

    def get(self):
        acc_count = 2 ** self.acc_power.get()
        log_count = self.log_size.get()
        total_count = acc_count + log_count
        if total_count == 0:
            return 0

        return acc_count / total_count * self.log.get() + acc_count / total_count * self.accumulator.get()

    def sample_count(self):
        acc_count = 2 ** self.acc_power.get()
        log_count = self.log_size.get()
        return acc_count + log_count

    def average(self, mat):
        # Initial accumulator fill
        if self.acc_power.get() == -1:
            self.accumulator.set(mat)
            self.acc_power.set(0)
            return

        acc_count = 2 ** self.acc_power.get()
        if self.log_size.get() + 1 == acc_count:
            # The log and the accumulator are averages of the same size, so combine
            # them into the accumulator as a simple average and reset the log.
            new_acc = (self.accumulator.get() + self.log.get() + mat / acc_count) / 2
            self.accumulator.set(new_acc)
            self.acc_power.incr(1)
            self.log_size.set(0)
            self.log.set(np.zeros_like(mat))
        else:
            # The log is not full, so average the new value and update the counts
            self.log.incr(mat / acc_count)
            self.log_size.incr(1)

class SerializedVariantState(SerializedState):

    def initialize(self, dimension):
        self.mle_weights.initialize(np.zeros((dimension,)))
        self.discriminitive_mask.initialize(np.zeros((dimension,), dtype='int8'))

        self.x_mean.initialize((dimension,))
        self.xx_mean.initialize((dimension,))

        for col in range(dimension):
            self.by_feature[col].initialize()

    def __init__(self, experiment_uuid_hex, base_path, variant):
        super().__init__()

        self.path = os.path.join(base_path, variant)

        self.mle_weights = self._serialized('w_mle.dat')
        self.discriminitive_mask = self._serialized('dm.dat')

        self.x_mean = self._field(StreamingAverage(self.path, 'x_mean'))
        self.xx_mean = self._field(StreamingAverage(self.path, 'xx_mean'))

        dimension = Schema.for_experiment(experiment_uuid_hex).dimension()

        self.by_feature = {
            col: self._field(SerializedFeatureState(experiment_uuid_hex, self.path, col))
            for col in range(dimension)
        }

class SerializedFeatureState(SerializedState):

    def initialize(self):
        self.II_mean.initialize((2, 2))
        self.Iy_mean.initialize((2,))

    def __init__(self, experiment_uuid_hex, base_path, col):
        super().__init__()

        self.path = os.path.join(base_path, str(col))

        self.II_mean = self._field(StreamingAverage(self.path, "II"))
        self.Iy_mean = self._field(StreamingAverage(self.path, "Iy"))

class SerializedExperimentState(SerializedState):

    @staticmethod
    def initialize(experiment_uuid_hex):
        ex = SerializedExperimentState(experiment_uuid_hex)
        dimension = Schema.for_experiment(experiment_uuid_hex).dimension()

        ex._state.initialize(np.array([0.5, 0, 0]))
        ex.outcome_counts.initialize(np.zeros((4,), 'int64'))
        for variant in VARIANTS:
            ex.by_variant[variant].initialize(dimension)

    def __init__(self, experiment_uuid_hex, variants=VARIANTS):
        super().__init__()

        self.path = os.path.join(config.get('stats_base_dir'), str(experiment_uuid_hex))

        # Fields
        self.outcome_counts = self._serialized('outcome_counts.dat')
        self.by_variant = {
            variant: self._field(SerializedVariantState(experiment_uuid_hex, self.path, variant))
            for variant in variants
        }
        self._state = self._serialized('sig_state.dat')
        (
            self.pr_b_gt_a,
            self.significance,
            self.reached_significance
        ) = [FieldAccessor(self._state, i) for i in range(3)]

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
