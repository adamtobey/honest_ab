import pytest

from honest_ab.database import *

# TODO tests will not catch methods not using @db_session when
# they should, since this transaction will supercede the one they
# should create. See if there is a fix for this.
@pytest.fixture(autouse=True)
def isolate_tests():
    with db_session(strict=True):
        yield
        rollback()
