import json
import numpy as np
from collections import defaultdict

from honest_ab.schema import Schema
from honest_ab.controllers import APP_KEY_URL_PARAM
from honest_ab.models import Experiment
from honest_ab.config import config
from honest_ab.compute import pp
from honest_ab.facades import ExperimentResults
from honest_ab.experiment_state import SerializedExperimentState
from honest_ab.experiment_constants import *

from .fixtures import *
from .predicates import *

class TestSufficientStatistics(object):

    schema = {
        "d": "numeric",
        "u": "numeric"
    }

    data = {
        ('a', 'success'): dict(d=100, u=10),
        ('a', 'success'): dict(d=112, u=10),
        ('a', 'failure'): dict(d=4, u=10),
        ('b', 'success'): dict(d=10, u=10),
        ('b', 'failure'): dict(d=100, u=10),
    }

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

    def test_variance(self, client):
        user = make_user()
        exp = make_experiment(user, self.schema)

        self.submit_data(self.data, exp, client)

        d = defaultdict(lambda: defaultdict(list))
        for (variant, outcome), data in self.data.items():
            for i, val in enumerate(data.values()):
                d[variant][i].append(val)

        ex = SerializedExperimentState(exp.get_pk().hex)
        for variant, data in d.items():
            v = ex.by_variant[variant]
            x_mean = v.x_mean.get()
            xx_mean = v.xx_mean.get()
            for i, values in sorted(data.items()):
                ref_var = np.var(values)
                acc_var = xx_mean[i] - x_mean[i] ** 2
                assert abs(ref_var - acc_var) < 1e-6
