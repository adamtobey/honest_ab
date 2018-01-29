import pytest
from flask_login import login_user

from test.fixtures import app, client, make_user
from test.helpers import *

from honest_ab.models import User, Experiment

class TestCreatingExperiments(object):

    @wrap_db
    def test_logging_in(self, client):
        user = make_user()

        lr = client.post('/users/perform_login', follow_redirects=True, data=dict(
            username = 'test',
            password = 'password'
        ))

        assert(b"Logged in" in lr.data)

        response = client.get('/users/identify')

        assert(b"test is logged in" in response.data)

        client.get('users/logout')

        assert(b"test is logged out")

    @wrap_db
    def test_requires_authentication(self, client):
        pass #TODO

    @wrap_db
    def test_fails_without_name(self, app, client):
        user = make_user()
        login_user(user)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='',
            description='Something'
        ))

        assert(b"Experiment must have a name" in response.data)

    @wrap_db
    def test_succeeds_without_description(self, client):
        pass

    @wrap_db
    def test_succeeds_with_description(self, client):
        pass

    @wrap_db
    def test_fails_with_duplicate_name(self, client):
        pass
