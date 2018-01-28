from pony.orm import *

db = Database()

# TODO keep in warning? Probably better way to isolate tests
def commit():
    raise RuntimeError("Potentially breaks test isolation. Remove this -> fix that")
