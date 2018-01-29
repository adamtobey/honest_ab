import pytest

from honest_ab.database import *

@pytest.fixture(autouse=True)
def isolate_tests():
    with db_session(strict=True):
        yield
        rollback()
