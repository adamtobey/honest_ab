import numpy as np

from ..experiment_state import SerializedExperimentState, VARIANTS, MLE_WEIGHTS, DISCRIMINITIVE_MASK, XX, XY

class DiscriminitiveFeatureModel(object):

    SY = 0.5
    CRITICAL_DISCRIMINITIVE_T = 1.96

    def __init__(self, experiment):
        self.ex = experiment

    def update(self, batches):
        for variant, (X, y) in batches.items():
            xx = self.ex.by_variant[variant][XX]
            xy = self.ex.by_variant[variant][XY]
            # TODO seems prone to overflows
            xx.incr(X.T @ X)
            xy.incr(np.dot(X.T, y))

            if self.ex.reached_significance.get(): # Reached significance
                cov = np.linalg.inv(xx.get()) * self.SY

                w_mle = self.ex.by_variant[variant][MLE_WEIGHTS]
                dm = self.ex.by_variant[variant][DISCRIMINITIVE_MASK]

                w_mle.set(cov @ xy.get() / self.SY)
                dmv = (abs(w_mle.get()) / np.diag(cov) > self.CRITICAL_DISCRIMINITIVE_T).astype('int8')
                dm.set(dmv)
