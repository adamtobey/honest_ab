from honest_ab.database import *
from functools import wraps

class SanityPreservationException(RuntimeError):
    pass

__db_session = db_session

# TODO creating models in fixtures breaks isolation :(
# Actually I forgot to use wrap_db... Test this later

# TODO find a way to ensure using wrap_db
def wrap_db(function):
    @wraps(function)
    @__db_session
    def isolate(*a, **b):
        function(*a, **b)
        rollback()
    return isolate

# To preserve test isolation, override the ability to commit transactions in tests
def commit():
    raise SanityPreservationException("Use flush() instead of commit().")

def db_session(function):
    raise SanityPreservationException("Use @wrap_db instead instead of @db_session.")
