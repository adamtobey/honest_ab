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

        self.ex.pr_b_gt_a.set(self._pr_b_gt_a(self.ex.outcome_counts.get()))
        self.ex.significance.set(max(self.ex.pr_b_gt_a.get(), 1 - self.ex.pr_b_gt_a.get()))
        if self.ex.significance.get() > self.CRITICAL_SIGNIFICANCE:
            self.ex.reached_significance.set(True)

    def _h(self, aA, bA, aB, bB, i):
        return np.exp(betaln(aA + i, bB + bA) - betaln(1 + i, bB) - betaln(aA, bA)) / (bB + i)

    def _pr_b_gt_a(self, outcome_counts):
        aA, bA, aB, bB = outcome_counts + 1
        return sum([self._h(aA, bA, aB, bB, i) for i in range(aB - 1)])
