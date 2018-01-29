import pytest

from test.fixtures import app, client, make_user, auth
from test.predicates import requires_authentication
from test.helpers import *

from honest_ab.models import User, Experiment

class TestCreatingExperiments(object):

    @wrap_db
    def test_requires_authentication(self, client):
        response = client.post('experiments/create', follow_redirects=False, data=dict(
            name='name',
            description='test'
        ))
        assert(requires_authentication(response))

    @wrap_db
    def test_fails_without_name(self, client, auth):
        user = make_user()
        auth.login(user)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='',
            description='Something'
        ))

        assert(b"Fail" in response.data)

    @wrap_db
    def test_succeeds_without_description(self, client, auth):
        user = make_user()
        auth.login(user)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='experiment',
            description=''
        ))

        assert(b"Experiment created" in response.data)

    @wrap_db
    def test_succeeds_with_description(self, client, auth):
        user = make_user()
        auth.login(user)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='experiment',
            description='being descriptive'
        ))

        assert(b"Experiment created" in response.data)

    @wrap_db
    def test_fails_with_duplicate_name(self, client, auth):
        user = make_user()
        auth.login(user)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='my experiment',
            description='Something'
        ))

        assert(b"Experiment created" in response.data)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='my experiment',
            description='Something else'
        ))

        assert(b"Fail" in response.data)

    @wrap_db
    def test_succeeds_with_duplicate_name_but_different_user(self, client, auth):
        user1 = make_user()
        user2 = make_user('bob')

        auth.login(user1)
        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='my experiment',
            description='Something'
        ))
        assert(b"Experiment created" in response.data)

        auth.login(user2)
        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='my experiment',
            description='Something else'
        ))
        assert(b"Experiment created" in response.data)
