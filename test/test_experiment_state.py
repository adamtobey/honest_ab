import numpy as np
import os

from honest_ab.experiment_state import StreamingAverage, SerializedState, SerializedMatrixAccessor
from honest_ab.config import config
from .fixtures import *
from .predicates import *

def test_streaming_average():
    avg = StreamingAverage(config.get('stats_base_dir'), 'test')
    avg.initialize((3, 3))

    N = 47
    acc = np.zeros((3,3))
    with avg:
        for i in range(N):
            rand = np.random.rand(3,3) * 10
            avg.average(rand)
            acc += rand / N

    assert np.allclose(acc, avg.get())

def test_serialized_matrix_accessor():
    mat = SerializedMatrixAccessor(config.get('stats_base_dir'), 'test')
    rand = np.random.rand(4, 5)
    mat.initialize(rand)

    assert np.allclose(mat.get(), rand)
    mat.persist()

    assert np.allclose(SerializedMatrixAccessor(config.get('stats_base_dir'), 'test').get(), rand)

    mat.get()[0,0] = 127
    mat.persist()

    assert mat.get()[0,0] == 127

    rand = np.random.rand(4, 5)
    mat.set(rand)

    assert np.allclose(mat.get(), rand)

    mat.incr(1)
    assert np.allclose(mat.get(), rand + 1)

def test_serialized_state():
    state = SerializedState()
    state.path = config.get('stats_base_dir')
    state.test = state._serialized('test')

    nested = SerializedState()
    nested.path = os.path.join(config.get('stats_base_dir'), 'nested')
    nested.test = nested._serialized('test')
    state.nested = state._field(nested)

    state.test.initialize(np.zeros((2,3)))
    rand = np.random.rand(4, 5)
    state.nested.test.initialize(rand)

    assert np.allclose(state.test.get(), np.zeros((2,3)))
    assert np.allclose(state.nested.test.get(), rand)

    rand = np.random.rand(4,5)
    with state:
        state.test.get()[1,1] = 49
        state.nested.test.set(rand)

    assert state.test.get()[1,1] == 49
    assert np.allclose(SerializedMatrixAccessor(os.path.join(config.get('stats_base_dir'), 'nested'), 'test').get(), rand)
