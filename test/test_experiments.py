import pytest

from test.fixtures import app, client, make_user, auth
from test.helpers import *

from honest_ab.models import User, Experiment

class TestCreatingExperiments(object):

    @wrap_db
    def test_logging_in(self, client, auth):
        user = make_user()

        auth.login(user)

        response = client.get('/users/identify')
        assert(b"test is logged in" in response.data)

        auth.logout()

        response = client.get('/users/identify')
        assert(b"Logged out" in response.data)

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
