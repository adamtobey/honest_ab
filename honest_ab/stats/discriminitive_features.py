import numpy as np

from ..experiment_state import SerializedExperimentState, VARIANTS, MLE_WEIGHTS, DISCRIMINITIVE_MASK, XX, XY

class DiscriminitiveFeatureModel(object):

    SY = 0.5
    CRITICAL_DISCRIMINITIVE_T = 1.96
    EPS = 1e-8

    def __init__(self, experiment):
        self.ex = experiment

    # WARNING: the average calculations here are unweighted averages of
    # batch averages, meaning that the batch size must be constant for the
    # average of averages to be the overall average. If the batch size changes,
    # or if flushes happen on incomplete batches, the averages will be wrong.
    def update(self, batches):
        for variant, (X, y) in batches.items():
            if X.shape[0] == 0:
                continue

            var = self.ex.by_variant[variant]

            var.x_mean.average(X.mean(axis=0))
            var.xx_mean.average((X ** 2).mean(axis=0))

            I = np.ndarray((X.shape[0], 2))
            I[:,1] = 1 # Trick to solve for bias
            for col in range(X.shape[1]):
                feat = var.by_feature[col]
                I[:,0] = X[:,col]

                # Keep sufficient statistics for Bayesian linear regression
                feat.II_mean.average(I.T @ I)
                feat.Iy_mean.average(I.T @ y)

            if self.ex.reached_significance.get():
                # Consider each feature discriminitive if its multiplicative weight is
                # not zero. Perform a T-test with null hypothesis H0: wi = 0, using
                # the Bayesian estimated variance of each weight. Solve for the bias
                # term only to normalize the feature, even though it's not explicitly used.
                x_mean = var.x_mean.get()
                xx_mean = var.xx_mean.get()

                mult_weights = np.ndarray(X.shape[1])
                mult_vars = np.ndarray(X.shape[1])
                for col in range(X.shape[1]):
                    feat = var.by_feature[col]

                    inv_f_var = (xx_mean[col] - x_mean[col] ** 2)

                    # For prior covariance, assume independence, i.e. diagonal matrix.
                    # Set bias variance to twice the mean of the data so that the bias
                    # to zero-center the data is well within that variance.
                    # Set weight variance to 1 / the data variance, with the assumption
                    # that for equally discriminitive features E[wTx] = 1.
                    # Represent the matrix inverse in place by taking the reciprocal
                    # along the diagonal for a diagonal matrix, assuming full rank.
                    v0_inv = np.array([
                        [inv_f_var, 0],
                        [0, 1 / (2 * x_mean[col] + self.EPS)]
                    ])

                    N = feat.II_mean.sample_count()
                    v_star = np.linalg.inv(self.SY / N * v0_inv + feat.II_mean.get())
                    vn = self.SY / N * v_star
                    wn = v_star @ feat.Iy_mean.get()

                    mult_weights[col] = wn[0]
                    mult_vars[col] = vn[0,0]

                mult_stdevs = np.sqrt(mult_vars)
                discriminitive_mask = (abs(mult_weights / mult_stdevs) > self.CRITICAL_DISCRIMINITIVE_T).astype('int8')

                var.mle_weights.set(mult_weights)
                var.discriminitive_mask.set(discriminitive_mask)
