from test.fixtures import app, client
from test.helpers import *

from honest_ab.models import User

class TestCreatingUsers(object):

    @wrap_db
    def test_fails_with_duplicate_user(self, client):
        user = User.create(
            username = 'my_organization',
            password_1 = 'somepass',
            password_2 = 'somepass',
        )

        flush()

        response = client.post('/users/create', data=dict(
            name = "my_organization",
            password_1 = "mypass",
            password_2 = "mypass"
        ))

        assert(b"This username is taken" in response.data)

        users = count(u for u in User if u.name == "my_organization")

        assert(users == 1)

    @wrap_db
    def test_succeeds_with_valid_user(self, client):
        response = client.post('/users/create', data=dict(
            name = "my_organization",
            password_1 = "mypass",
            password_2 = "mypass"
        ))

        assert(b"Your account was created" in response.data)

        user = get(u for u in User if u.name == "my_organization")

        assert(user != None)

    @wrap_db
    def test_fails_with_non_matching_passwords(self, client):
        response = client.post('/users/create', data=dict(
            name = "my_organization",
            password_1 = "mypass",
            password_2 = "lakdjf"
        ))

        assert(b"Passwords did not match" in response.data)

        user = get(u for u in User if u.name == "my_organization")

        assert(user == None)

    @wrap_db
    def test_fails_with_blank_username(self, client):
        response = client.post('/users/create', data=dict(
            name = "",
            password_1 = "mypass",
            password_2 = "mypass"
        ))

        assert(b"Must provide a username" in response.data)

        user = get(u for u in User if u.name == "my_organization")

        assert(user == None)

    @wrap_db
    def test_fails_with_short_password(self, client):
        response = client.post('/users/create', data=dict(
            name = "my_organization",
            password_1 = "abc",
            password_2 = "abc"
        ))

        assert(b"Password must be at least 4 characters" in response.data)

        user = get(u for u in User if u.name == "my_organization")

        assert(user == None)
