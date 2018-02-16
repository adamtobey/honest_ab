import pytest

from test.fixtures import app, client, make_user, auth
from test.predicates import requires_authentication

from honest_ab.models import User, Experiment
from honest_ab.database import select
from honest_ab.schemas import get_experiment_schema

class TestCreatingExperiments(object):

    # TODO test schema creation

    def schema_to_form_fields(self, schema):
        form_encoded = {}
        for i, (name, tt) in enumerate(schema.items()):
            form_encoded[f"schema_field_{i}_name"] = name
            form_encoded[f"schema_field_{i}_type"] = tt
        return form_encoded

    def test_valid_schema(self, client, auth):
        user = make_user()
        auth.login(user)

        schema = {
            'field_1': "numeric",
            'field_2': "numeric"
        }

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='name',
            description='test',
            **self.schema_to_form_fields(schema)
        ))

        experiment = select(ex for ex in Experiment if ex.name == 'name').first()
        eid = experiment.get_pk().hex

        assert schema == get_experiment_schema(eid)

    # TODO test an invalid schema when schema validation is implemented

    def test_requires_authentication(self, client):
        response = client.post('experiments/create', follow_redirects=False, data=dict(
            name='name',
            description='test'
        ))
        assert(requires_authentication(response))

    def test_fails_without_name(self, client, auth):
        user = make_user()
        auth.login(user)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='',
            description='Something'
        ))

        assert(b"must have a name" in response.data)

    def test_succeeds_without_description(self, client, auth):
        user = make_user()
        auth.login(user)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='experiment',
            description=''
        ))

        assert(b"Experiment created" in response.data)

    def test_succeeds_with_description(self, client, auth):
        user = make_user()
        auth.login(user)

        response = client.post('experiments/create', follow_redirects=True, data=dict(
            name='experiment',
            description='being descriptive'
        ))

        assert(b"Experiment created" in response.data)

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

        assert(b"names must be unique" in response.data)

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
