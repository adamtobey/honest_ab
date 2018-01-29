from flask_login import current_user, login_user, logout_user, login_required, LoginManager, UserMixin
from honest_ab.database import in_transaction
from honest_ab.models import User

_current_user = current_user

# Flask login uses a Workzeug LocalProxy to pretend current_user
# is a local, which becomes extremely misleading. For example,
# isinstance(current_user, User) is always False even when a user
# is logged in. Replace that with a transparent function that doesn't
# require reading the plugin source to figure out why your reasonable
# code doesn't work.
def current_user():
    # The user from _current_user is cached from a transaction that has
    # since been closed, so if it's being accessed inside a transaction,
    # it must be reloaded from the database to avoid violating the transaction
    # isolation and throwing an error
    if in_transaction():
        return User[_current_user.get_pk()]
    else:
        return _current_user._get_current_object()
