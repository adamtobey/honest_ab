from honest_ab.database import *
from functools import wraps

class SanityPreservationException(RuntimeError):
    pass

__db_session = db_session

def wrap_db(function):
    @wraps(function)
    def isolate(*a, **b):
        function(*a, **b)
        rollback()
    return __db_session(isolate)

# To preserve test isolation, override the ability to commit
# transactions in tests
def commit():
    raise SanityPreservationException("Use flush() instead of commit().")

def db_session(function):
    raise SanityPreservationException("Use @wrap_db instead instead of @db_session.")