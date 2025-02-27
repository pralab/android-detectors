"""
.. moduleauthor:: Daniele Angioni <daniele.angioni@unica.it>
"""
from secml.array import CArray
from secml.core.constants import inf
from models.secsvm.secsvm import SecSVM
from sklearn.svm import LinearSVC
import numpy as np
import pandas as pd


class SVMCustomBounds(SecSVM):
    """Secure Support Vector Machine (Sec-SVM) classifier.
    Support Vector Machine with Custom Bounds (SVM-CB) classifier

    This implements the time-aware classifier from:

     Angioni et al. "Robust Machine Learning for Malware Detection over Time."
     ITASEC 2022. https://ceur-ws.org/Vol-3260/paper12.pdf

    Parameters
        ----------
        C : float, optional
            Penalty hyper-parameter C of the error term. Default 1.0.
        kernel : None or CKernel subclass, optional
            Instance of a CKernel subclass to be used for computing
            similarity between patterns. If None (default), a linear
            SVM is trained in the primal; otherwise an SVM is trained in the dual,
            using the precomputed kernel values.
        class_weight : {dict, 'balanced', None}, optional
            Set the parameter C of class i to `class_weight[i] * C`.
            If not given (default), all classes are supposed to have
            weight one. The 'balanced' mode uses the values of labels to
            automatically adjust weights inversely proportional to
            class frequencies as `n_samples / (n_classes * np.bincount(y))`.
        ub : scalar or None, optional
            Upper bound of the weights. If None (default), no bound is applied.
        idx_ub : CArray or None, optional
            If CArray, the upper bound is only applied to the weights indicized
            by `idx_ub`. If None (default), the bound is applied automatically to the unstable features weights.
        lb : scalar or None, optional
            Lower bound of the weights. If None (default), no bound is applied.
        idx_lb : CArray or None, optional
            If CArray, the lower bound is only applied to the weights indicized
            by `idx_ub`. If None (default), the bound is applied automatically to the unstable features weights.
        eta : scalar, optional
            Step of the gradient descent. Default 0.5.
        max_it : int, optional
            Maximum number of iterations of the gradient descent. Default 1e4.
        eps : scalar, optional
            Tolerance of the stop criterion of the gradient descent. Default 1e-4.
    """

    def __init__(self, C=0.1, kernel=None, class_weight=None,
                 ub=inf, idx_ub=None,
                 lb=-inf, idx_lb=None,
                 n_unstable_features=100,
                 eta=0.5, max_it=1e4,
                 eps=1e-4):
        SecSVM.__init__(self, C=C,
                        kernel=kernel,
                        class_weight=class_weight,
                        eta=eta,
                        max_it=max_it,
                        eps=eps,
                        ub=ub, idx_ub=idx_ub,
                        lb=lb, idx_lb=idx_lb)

        self.n_unstable_features = n_unstable_features
        self._w_bs = None   # baseline weights
        self._f_slopes = None   # feature slopes
        self._tstab = None  # T-stability vector

    def _get_baseline_weights(self, X, y):
        clf = LinearSVC(C=self.C)
        clf.fit(X, y)
        return clf.coef_.flatten()

    def _get_feature_slopes(self, X, t, n_months=1):
        df = pd.DataFrame({'id': np.arange(t.size), 't': t})
        idxs_per_month = df.groupby(df["t"].dt.to_period("M"))["id"].apply(list)
        idxs_per_month = [np.array(idxs)
                          for idxs in idxs_per_month]

        # Group samples based on a <n_months> time window
        X_t = [X[np.concatenate(idxs_per_month[k:k+n_months])]
                    for k in range(0, len(idxs_per_month), n_months)]

        # avg_features_t.shape = (n_splits, n_features)
        avg_features_t = np.concatenate([Xk.mean(axis=0) for Xk in X_t])
        t_ = np.arange(len(X_t))

        # One slope value for each feature, obtained with Least squares polynomial fit
        slopes, _ = np.polyfit(t_, avg_features_t, deg=1)

        return slopes

    def compute_tstabilty(self, X, y, t):
        self._w_bs = self._get_baseline_weights(X, y)
        self._f_slopes = self._get_feature_slopes(X, t)
        self._tstab = self._w_bs * self._f_slopes
        return self._tstab


    def fit(self, features, y, t):
        """
        Overriding fit method of SecSVM...

        Parameters
        ----------
        features: iterable of iterables of strings
            Iterable of shape (n_samples, n_features) containing textual
            features in the format <feature_type>::<feature_name>.
        y : np.ndarray
            Array of shape (n_samples,) containing the class labels.
        t : np.ndarray
            Array of shape (n_samples,) containing the timestamps.
        """
        X = self._vectorizer.fit_transform(features)
        self._input_features = (self._vectorizer.get_feature_names_out()
                                .tolist())

        tstab = self.compute_tstabilty(X, y, t)
        self._unst_feat_idxs = np.argsort(tstab)[:self.n_unstable_features]
        # Select the indices of the most unstable features (most negative ones) that must be bounded
        self._idx_lb = CArray(self._unst_feat_idxs)
        self._idx_ub = CArray(self._unst_feat_idxs)

        self._fit(X, y)
