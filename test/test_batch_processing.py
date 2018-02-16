import json
import numpy as np
from pdb import set_trace

from honest_ab.serialization import serialize_matrix, deserialize_matrix, experiment_path
from honest_ab.schemas import store_experiment_schema
from honest_ab.controllers import APP_KEY_URL_PARAM
from honest_ab.models import Experiment
from honest_ab.config import config
from honest_ab.compute import pp

from .fixtures import *
from .predicates import *

class TestRegressionUpdates(object):

    # TODO this should be a fixture
    schema = {
        "d": "numeric",
        "u": "numeric"
    }

    def make_experiment(self, user, schema=schema):
        return Experiment.create_with_schema(
            name="Test Experiment",
            user=user,
            schema=schema
        )

    def submit_data(self, data, experiment, client, force_flushes=2):
        if force_flushes:
            _bs = config.get('batch_size')
            config['batch_size'] = int(len(data) // force_flushes)
        try:
            for (variant, result), point in data.items():
                client.post(f'/api/v1/experiments/{experiment.get_pk().hex}/{variant}/{result}?{APP_KEY_URL_PARAM}={experiment.user.app_key.hex}', data=point)
        finally:
            if force_flushes:
                config['batch_size'] = _bs
                assert len(pp.submits) >= 2

    def encode_batches(self, data):
        batches = dict(a=([], []), b=([], []))
        for (variant, result), point in data.items():
            X, y = batches[variant]
            X.append(np.array(list(point.values())))
            y.append(result == 'success')
        return {
            variant: (np.array(X), np.array(y))
            for variant, (X, y) in batches.items()
        }

    def reference_regression(self, X, y, inv_cov_init, mu_init, sy):
        cov = sy * np.linalg.inv(sy * inv_cov_init + X.T @ X)
        mu = cov @ inv_cov_init @ mu_init + cov @ X.T @ y / sy
        return cov, mu

    def test_regression_update(self, client):
        user = make_user()
        ex = self.make_experiment(user)

        data = {
            ('a', 'success'): dict(d=100, u=10),
            ('a', 'success'): dict(d=112, u=10),
            ('a', 'failure'): dict(d=4, u=10),
            ('b', 'success'): dict(d=10, u=10),
            ('b', 'failure'): dict(d=100, u=10),
        }
        self.submit_data(data, ex, client)
        batches = self.encode_batches(data)

        regression_path = experiment_path(ex.get_pk().hex)

        sy = 0.5
        inv_cov_init = np.identity(2)
        mu_init = np.zeros((2,))

        for variant, (X, y) in batches.items():
            xx = deserialize_matrix(regression_path, variant, 'xx.dat')
            xy = deserialize_matrix(regression_path, variant, 'xy.dat')

            # TODO use the route that actually gives these computations to test
            # end to end when that's implemented
            cov = np.linalg.inv(sy * inv_cov_init + xx) * sy
            mu = cov @ inv_cov_init @ mu_init + cov @ xy / sy

            rcov, rmu = self.reference_regression(X, y, inv_cov_init, mu_init, sy)

            assert np.allclose(cov, rcov)
            assert np.allclose(mu, rmu)
