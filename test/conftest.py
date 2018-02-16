import os
import pytest
from tempfile import TemporaryDirectory

# Mock out the processing thread pool
from honest_ab.config import config
config['testing'] = True
from honest_ab.compute import pp

from honest_ab.database import *
from honest_ab.redis import rd

# TODO tests will not catch methods not using @db_session when
# they should, since this transaction will supercede the one they
# should create. See if there is a fix for this.
@pytest.fixture(autouse=True)
def isolate_tests():
    pp.reset()
    rd.flushall()
    with TemporaryDirectory() as td:
        config['stats_base_dir'] = td
        with db_session(strict=True):
            yield
            rollback()
