from flask_login import current_user, login_user, logout_user, login_required, LoginManager, UserMixin

_current_user = current_user

# Flask login uses a Workzeug LocalProxy to pretend current_user
# is a local, which becomes extremely misleading. For example,
# isinstance(current_user, User) is always False even when a user
# is logged in. Replace that with a transparent function that doesn't
# require reading the plugin source to figure out why your reasonable
# code doesn't work.
def current_user():
    return _current_user._get_current_object()
