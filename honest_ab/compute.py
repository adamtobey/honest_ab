from concurrent.futures import ThreadPoolExecutor, Future

from .config import config

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

# TODO for seeing errors
pp = PoolMock()

# if config.get('testing'):
#     pp = PoolMock()
# else:
#     pp = ThreadPoolExecutor()
