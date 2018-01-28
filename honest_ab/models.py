from flask_login.mixins import UserMixin

from honest_ab.database import *
from honest_ab.crypto import password_context

class AuthenticationError(RuntimeError):
    pass

class User(db.Entity, UserMixin):

    name = Required(str)
    pass_hash = Required(str)

    # TODO mixin if useful
    def find_by_id(id):
        return get(u for u in User if u.id == id)

    @staticmethod
    @db_session
    def create(username, password_1, password_2):
        if password_1 != password_2:
            raise AuthenticationError("Passwords did not match")
        if (type(username) != str) or len(username) < 1:
            raise AuthenticationError("Must provide a username")
        if (type(password_1) != str) or len(password_1) < 4:
            raise AuthenticationError("Password must be at least 4 characters")
        if count(u for u in User if u.name == username) > 0:
            raise ValueError("This username is taken")

        pass_hash = password_context.hash(password_1)
        user = User(name=username, pass_hash=pass_hash)

        flush() #?

        return user
