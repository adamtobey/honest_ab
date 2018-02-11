import uuid
from flask_login.mixins import UserMixin

from honest_ab.database import *
from honest_ab.crypto import password_context

# TODO create, update timestamps?

# Users

class AuthenticationError(RuntimeError):
    pass

class User(db.Entity, UserMixin):

    # TODO string length validation
    name = Required(str, unique=True)
    pass_hash = Required(str)

    app_key = Required(uuid.UUID, default=uuid.uuid4)

    experiments = Set('Experiment')

    # TODO this already exists: User[pkey]
    @db_session
    def find_by_id(id):
        return get(u for u in User if u.id == id)

    # Required for flask_login. This will be the ID stored in the
    # Session and will be used later to look up the user by according
    # to the function registered with the LoginManager.
    def get_id(self):
        return str(self.get_pk())

    def application_key(self):
        return self.app_key.hex

    @staticmethod
    @db_session
    def for_login(username, password):
        if (type(username) != str) or len(username) < 1:
            raise AuthenticationError("Invalid username")
        if (type(password) != str) or len(password) < 1:
            raise AuthenticationError("Invalid password")

        user = get(u for u in User if u.name == username)

        if user == None:
            raise AuthenticationError("Invalid username")

        if password_context.verify(password, user.pass_hash):
            return user
        else:
            raise AuthenticationError("Password is incorrect")

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

# Experiments

class Experiment(db.Entity):

    # Primary key & UUID used for associating observations with
    # experiments in data storage
    uuid = PrimaryKey(uuid.UUID, default=uuid.uuid4)

    # TODO string length validation
    name = Required(str)
    user = Required(User, index=True)

    # Names must be unique for each user
    composite_key(name, user)

    # TODO length
    description = Optional(str)
