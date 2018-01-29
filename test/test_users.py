import pytest

from test.fixtures import app, client

from honest_ab.models import User
from honest_ab.database import *

class TestIds(object):

    def test_can_find_user_by_id_for_login_manager(self, client):
        user = User.create(
            username = 'Joe',
            password_1 = 'mittens1982',
            password_2 = 'mittens1982'
        )
        flush()

        assert int(user.get_id()) == user.get_pk()

        lookup = User.find_by_id(user.get_id())
        assert lookup == user

# TODO test whether users are actually logged in with flask-login
# Perhaps by subscribing to the login signal, mocking the module,
# or reading the session in the app context

class TestLoggedOut(object):

    def test_logging_out_works_with_user(self, client):
        user = User.create(
            username = 'John',
            password_1 = '9898dhfaksh723SS@',
            password_2 = '9898dhfaksh723SS@'
        )
        flush()

        response = client.get('/users/perform_logout', follow_redirects=True)

        assert(b"Logged out" in response.data)

class TestLogginIn(object):

    def make_user(self, username='my_organization', password='somepass'):
        user = User.create(
            username = username,
            password_1 = password,
            password_2 = password,
        )
        flush()
        return user

    def test_fails_with_wrong_password(self, client):
        user = self.make_user()

        response = client.post('/users/perform_login', follow_redirects=True, data=dict(
            username = 'my_organization',
            password = 'password'
        ))

        assert(b"Password is incorrect" in response.data)

    def test_fails_with_nonexistent_username(self, client):
        user = self.make_user()

        response = client.post('/users/perform_login', follow_redirects=True, data=dict(
            username = 'nonexistent',
            password = 'password'
        ))

        assert(b"Invalid username" in response.data)

    def test_fails_with_blank_password(self, client):
        user = self.make_user()

        response = client.post('/users/perform_login', follow_redirects=True, data=dict(
            username = 'my_organization',
            password = ''
        ))

        assert(b"Invalid password" in response.data)

    def test_fails_with_blank_form(self, client):
        user = self.make_user()

        response = client.post('/users/perform_login', follow_redirects=True, data=dict(
            username = '',
            password = ''
        ))

        assert(b"Invalid username" in response.data)

    def test_fails_with_right_pass_wrong_user(self, client):
        user1 = self.make_user()
        user2 = self.make_user('Bob', 'securepass123')

        response = client.post('/users/perform_login', follow_redirects=True, data=dict(
            username = 'my_organization',
            password = 'securepass123'
        ))

        assert(b"Password is incorrect" in response.data)

    def test_succeeds_with_username_password(self, client):
        user = self.make_user()

        response = client.post('/users/perform_login', follow_redirects=True, data=dict(
            username = 'my_organization',
            password = 'somepass'
        ))

        assert(b"Logged in" in response.data)

class TestCreatingUsers(object):

    def test_fails_with_duplicate_user(self, client):
        user = User.create(
            username = 'my_organization',
            password_1 = 'somepass',
            password_2 = 'somepass',
        )

        flush()

        response = client.post('/users/create', follow_redirects=True, data=dict(
            name = "my_organization",
            password_1 = "mypass",
            password_2 = "mypass"
        ))

        assert(b"This username is taken" in response.data)

        users = count(u for u in User if u.name == "my_organization")

        assert(users == 1)

    def test_succeeds_with_valid_user(self, client):
        response = client.post('/users/create', follow_redirects=True, data=dict(
            name = "my_organization",
            password_1 = "mypass",
            password_2 = "mypass"
        ))

        assert(b"Your account was created" in response.data)

        user = get(u for u in User if u.name == "my_organization")

        assert(user != None)

    def test_fails_with_non_matching_passwords(self, client):
        response = client.post('/users/create', follow_redirects=True, data=dict(
            name = "my_organization",
            password_1 = "mypass",
            password_2 = "lakdjf"
        ))

        assert(b"Passwords did not match" in response.data)

        user = get(u for u in User if u.name == "my_organization")

        assert(user == None)

    def test_fails_with_blank_username(self, client):
        response = client.post('/users/create', follow_redirects=True, data=dict(
            name = "",
            password_1 = "mypass",
            password_2 = "mypass"
        ))

        assert(b"Must provide a username" in response.data)

        user = get(u for u in User if u.name == "my_organization")

        assert(user == None)

    def test_fails_with_short_password(self, client):
        response = client.post('/users/create', follow_redirects=True, data=dict(
            name = "my_organization",
            password_1 = "abc",
            password_2 = "abc"
        ))

        assert(b"Password must be at least 4 characters" in response.data)

        user = get(u for u in User if u.name == "my_organization")

        assert(user == None)
