from .pydantic_models import *
from sklearn.utils._array_api import get_namespace
from detectors.drebin.base_drebin import BaseDREBIN
from sklearn.svm import LinearSVC


class DREBIN(BaseDREBIN):
    """
    Implements the DREBIN classifier from:
      Arp, Daniel, et al. "Drebin: Effective and explainable detection of
      android malware in your pocket." NDSS 2014.
      https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf
    """

    def __init__(self, init_args: DrebinInit):
        """

        Parameters
        ----------
        init_args : DrebinInit
        """
        BaseDREBIN.__init__(self, init_args)
        self.linear = LinearSVC(**init_args.model_dump())

    def _train(self, X, y):
        self.linear.fit(X, y)
    
    def predict(self, features: list[str]) -> BaseClassifyResponse:
        X = self._vectorizer.transform(features)
        xp, _ = get_namespace(X)
        scores = self.linear.decision_function(X)
        if len(scores.shape) == 1:
            indices = xp.astype(scores > 0, int)
        else:
            indices = xp.argmax(scores, axis=1)

        return BaseClassifyResponse(
            labels=xp.take(self.linear.classes_, indices, axis=0).tolist(),
            scores=scores.tolist())
