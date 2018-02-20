from scipy.special import betaln
import numpy as np

from ..experiment_state import VARIANTS

class SignificanceModel(object):

    EPS = 1e-8
    CRITICAL_SIGNIFICANCE = 0.95

    def __init__(self, experiment_state):
        self.ex = experiment_state

    def update(self, batches):
        y_a, y_b = [batches[variant][1] for variant in VARIANTS]
        a_pos, b_pos = np.sum(y_a == 1), np.sum(y_b == 1)
        a_neg, b_neg = np.sum(y_a == 0), np.sum(y_b == 0)

        self.ex.outcome_counts.incr(np.array([a_pos, a_neg, b_pos, b_neg]))

        self.ex.b_loss.set(self._b_loss(*self.ex.outcome_counts.get()))
        self.ex.significance.set(2 * abs(0.5 - self.ex.b_loss.get()))
        if self.ex.significance.get() > self.CRITICAL_SIGNIFICANCE:
            # TODO introduce priors for regression model
            self.ex.reached_significance.set(True)


    def _hh(self, a, b, c, d, j):
        return np.exp(betaln(a + j, b + d) - np.log(d + j) - betaln(1 + j, d) - betaln(a, b))

    def _h(self, a, b, c, d):
        return 1 - sum([self._hh(a, b, c, d, j) for j in range(c)])

    def _br(self, x, y):
        return np.exp(betaln(x + 1, y) - betaln(x, y))

    def _stable_zeros(self, *X):
        return [self.EPS if x == 0 else x for x in X]

    def _b_loss(self, a_pos, a_neg, b_pos, b_neg):
        a_pos, a_neg, _b_pos, b_neg = self._stable_zeros(a_pos, a_neg, b_pos, b_neg)
        return max(0, self._br(a_pos, a_neg) * self._h(a_pos + 1, a_neg, b_pos, b_neg) - self._br(_b_pos, b_neg) * self._h(a_pos, a_neg, b_pos + 1, b_neg))
