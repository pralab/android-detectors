from sklearn.utils._array_api import get_namespace
from models.base import BaseDREBIN
from sklearn.svm import LinearSVC


class DREBIN(BaseDREBIN, LinearSVC):
    """
    Implements the DREBIN classifier from:
      Arp, Daniel, et al. "Drebin: Effective and explainable detection of
      android malware in your pocket." NDSS 2014.
      https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf
    """

    def __init__(self, tol=1e-4, C=0.1, class_weight=None, verbose=0,
                 random_state=0, max_iter=1000):
        """

        Parameters
        ----------
        tol : float, default=1e-4
            Tolerance for stopping criteria.
        C : float, default=0.1
            Regularization parameter. The strength of the regularization is
            inversely proportional to C. Must be strictly positive.
        class_weight : dict or 'balanced', default=None
            Set the parameter C of class i to ``class_weight[i]*C`` for
            SVC. If not given, all classes are supposed to have
            weight one.
            The "balanced" mode uses the values of y to automatically adjust
            weights inversely proportional to class frequencies in the input data
            as ``n_samples / (n_classes * np.bincount(y))``.
        verbose : int, default=0
            Enable verbose output. Note that this setting takes advantage of a
            per-process runtime setting in liblinear that, if enabled, may not work
            properly in a multithreaded context.
        random_state : int, RandomState instance or None, default=None
            Controls the pseudo random number generation for shuffling the data for
            the dual coordinate descent (if ``dual=True``). When ``dual=False`` the
            underlying implementation of :class:`LinearSVC` is not random and
            ``random_state`` has no effect on the results.
            Pass an int for reproducible output across multiple function calls.
            See :term:`Glossary <random_state>`.
        max_iter : int, default=1000
            The maximum number of iterations to be run.
        """
        BaseDREBIN.__init__(self)
        LinearSVC.__init__(
            self, tol=tol, C=C, fit_intercept=False, class_weight=class_weight,
            verbose=verbose, random_state=random_state, max_iter=max_iter)

    def _fit(self, X, y):
        LinearSVC.fit(self, X, y)
    
    def predict(self, features):
        X = self._vectorizer.transform(features)
        xp, _ = get_namespace(X)
        scores = self.decision_function(X)
        if len(scores.shape) == 1:
            indices = xp.astype(scores > 0, int)
        else:
            indices = xp.argmax(scores, axis=1)

        return xp.take(self.classes_, indices, axis=0), scores
