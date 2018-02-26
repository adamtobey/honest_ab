from pony.orm import *

db = Database()

def in_transaction():
    try:
        db.get_connection()
        return True
    except TransactionError:
        return False

def commit():
    raise RuntimeError("Potentially breaks test isolation. Remove this -> fix that")
