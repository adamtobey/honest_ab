from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock
from collections import defaultdict

from .config import config

class ExperimentLock(object):

    _active_locks = defaultdict(Lock)

    def __init__(self, experiment_id):
        self.lock = ExperimentLock._active_locks[experiment_id]

    def acquire(self):
        return self.lock.acquire()

    def release(self):
        return self.lock.release()

# Only mocking as needed
class PoolMock(object):

    def __init__(self):
        self.reset()

    def submit(self, fn, *args, **kwargs):
        self.submits.append((fn.__qualname__, args, kwargs))
        future = Future()
        future.set_result(fn(*args, **kwargs))
        return future

    def reset(self):
        self.submits = []

if config.get('testing'):
    pp = PoolMock()
else:
    pp = ThreadPoolExecutor()
