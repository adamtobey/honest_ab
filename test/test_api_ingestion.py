import json

from honest_ab.schemas import store_experiment_schema
from honest_ab.controllers import APP_KEY_URL_PARAM
from honest_ab.models import Experiment
from honest_ab.compute import pp
from honest_ab.config import config
from honest_ab.processing import _pop_batch

from .fixtures import *
from .predicates import *

class TestApiIngestion(object):

    schema = {
        "Cool Field": "numeric"
    }

    payload = {
        "Cool Field": "12"
    }

    def make_route(self, experiment, key=None, variant="a", result="success"):
        route = f"/api/v1/experiments/{experiment.get_pk().hex}/{variant}/{result}"
        if key:
            route = f"{route}?{APP_KEY_URL_PARAM}={key}"
        return route

    def make_experiment(self, user, schema=schema):
        return Experiment.create_with_schema(
            name="Test Experiment",
            user=user,
            schema=schema
        )

    def test_requires_authentication(self, client):
        response = client.post(self.make_route(self.make_experiment(make_user())), data=self.payload)

        assert requires_app_key(response)

    def test_404s_with_valid_experiment_wrong_user(self, client):
        user1 = make_user()
        user2 = make_user("Joe")
        ex_u2 = self.make_experiment(user2)
        route = self.make_route(ex_u2, user1.application_key())

        response = client.post(route, data=self.payload)

        assert response.status_code == 404

    def test_400s_with_variant_not_a_or_b(self, client):
        user = make_user()
        ex = self.make_experiment(user)
        route = self.make_route(ex, user.application_key(), variant="C")

        response = client.post(route, data=self.payload)

        assert response.status_code == 400

    def test_400s_with_result_not_success_or_failure(self, client):
        user = make_user()
        ex = self.make_experiment(user)
        route = self.make_route(ex, user.application_key(), result="maybe")

        response = client.post(route, data=self.payload)

        assert response.status_code == 400

    def test_400s_with_missing_data(self, client):
        user = make_user()
        ex = self.make_experiment(user)
        route = self.make_route(ex, user.application_key())

        response = client.post(route, data=dict(wrong_key="doesn't matter"))

        assert response.status_code == 400

    def test_stores_data_point_and_ignores_extra_features(self, client):
        user = make_user()
        ex = self.make_experiment(user)
        route = self.make_route(ex, user.application_key())

        response = client.post(route, data={'extra': 'ok', **self.payload})

        assert response.status_code == 200

        data = _pop_batch(ex.get_pk().hex)
        pl = json.loads(data[0].decode('utf-8'))

        for key, val in self.payload.items():
            assert pl[key] == val

        assert 'extra' not in data

    def test_writeahead_is_flushed_each_batch(self, client):
        _batches = config.get('batch_size')
        try:
            config['batch_size'] = 1
            user = make_user()
            ex = self.make_experiment(user)
            route = self.make_route(ex, user.application_key())

            client.post(route, data={'extra': 'ok', **self.payload})
            response = client.post(route, data={'extra': 'ok', **self.payload})

            assert response.status_code == 200

            assert len(pp.submits) == 2
            assert pp.submits[0][0] == 'process_batch'
            assert pp.submits[0][2]['experiment_uuid_hex'] == ex.get_pk().hex
        finally:
            config['batch_size'] = _batches
