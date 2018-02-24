from datetime import datetime
from collections import defaultdict
import numpy as np
import uuid

from .models import Experiment
from .experiment_state import SerializedExperimentState
from .experiment_constants import *

# TODO test
class ExperimentResults(object):

    def __init__(self, experiment_uuid_hex):
        self.id = experiment_uuid_hex
        self.experiment = Experiment[self.id]
        self.ex = SerializedExperimentState(self.id)

        self.name = self.experiment.name
        a_pos, b_pos, a_neg, b_neg = self.ex.outcome_counts.get()
        self.variants = {
            'Hits': (a_pos + a_neg, b_pos + b_neg),
            'Successes': (a_pos, b_pos),
            'Failures': (a_neg, b_neg),
            'Estimated Fitness': self._fitness(a_pos, a_neg, b_pos, b_neg)
        }
        self.summary = {
            'Running for': self._test_duration(),
            'Observations': a_pos + a_neg + b_pos + b_neg,
            'Significance': self._format_decimal(self.ex.significance.get()),
            'Reached significance': 'Yes' if self.ex.reached_significance.get() else 'No'
        }
        self.details = {
            'API ID': self.id,
            'Description': self.experiment.description
        }
        self.insights = self._insights() if self.ex.reached_significance.get() else None

    def _fitness(self, a_pos, a_neg, b_pos, b_neg):
        all_a = a_pos + a_neg
        all_b = b_pos + b_neg
        if all_a > 0:
            a_fit = self._format_decimal(a_pos / all_a)
        else:
            a_fit = "N/A"
        if all_b > 0:
            b_fit = self._format_decimal(b_pos / all_b)
        else:
            b_fit = "N/A"
        return (a_fit, b_fit)

    def _pp_sign(self, x):
        if x > 0:
            return "Positive"
        else:
            return "Negative"

    # TODO refactor and modularize for testing
    def _insights(self):
        out = {}
        ind = defaultdict(defaultdict)
        for variant in VARIANTS:
            mu = self.ex.by_variant[variant].mle_weights.get()
            dm = self.ex.by_variant[variant].discriminitive_mask.get()
            for i, pair in enumerate(zip(mu, dm)):
                ind[i][variant] = pair

        def discriminitive_for_one(mu, feature, variant):
            return f"{self._pp_sign(mu)} {feature} significantly correlates with success of {variant}"

        for feature, comp in ind.items():
            a_mu, a_dm = comp[VARIANTS[0]]
            b_mu, b_dm = comp[VARIANTS[1]]
            if a_dm and b_dm: # Discriminitive for both variants
                if np.sign(a_mu) == np.sign(b_mu): # Same correlation
                    out[feature] = f"{self._pp_sign(a_mu)} {feature} significantly correlates with success for both variants."
                else: # Opposite correlation
                    if a_dm > 0:
                        preference = "A over B"
                    else:
                        preference = "B over A"
                    out[feature] = f"Positive {feature} significantly correlates with preference of {preference}"
            elif a_dm:
                out[feature] = discriminitive_for_one(a_mu, feature, 'a')
            elif b_dm:
                out[feature] = discriminitive_for_one(b_mu, feature, 'b')
            # Otherwise not discriminitive

        return out

    def _format_decimal(self, x):
        return "{0:.2f}".format(x)

    def _test_duration(self):
        delta = datetime.now() - self.experiment.created_at
        delta_days = delta.days
        years = int(delta_days // 365)
        weeks = int((delta_days % 365) // 7)
        days = int(delta_days % 7)
        duration = []
        if years > 1:
            duration.append(f"{years} years")
        if weeks > 1:
            duration.append(f"{weeks} weeks")
        if days > 1:
            duration.append(f"{days} days")
        if len(duration) > 0:
            return ", ".join(duration)
        else:
            return "Less than a day"
