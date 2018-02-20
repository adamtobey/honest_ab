from datetime import datetime
from collections import defaultdict
import uuid

from .models import Experiment
from .experiment_state import SerializedExperimentState

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
            'Estimated Fitness': (1 - self.ex.b_loss.get(), self.ex.b_loss.get())
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
            mu = self.ex.by_variant[variant][W_MLE].get()
            dm = self.ex.by_variant[variant][DISCRIMINITIVE_MASK].get()
            for i, pair in enumerate(zip(dm, mu)):
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
        return x #TODO

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
