from pony.orm import *

db = Database()

# TODO not the most elegant solution
def in_transaction():
    try:
        db.get_connection()
        return True
    except TransactionError:
        return False

# TODO keep in warning? Probably better way to isolate tests
def commit():
    raise RuntimeError("Potentially breaks test isolation. Remove this -> fix that")
