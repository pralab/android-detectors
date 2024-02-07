from sklearn.feature_extraction.text import CountVectorizer
from models.base import BaseModel
import dill as pkl
from feature_extraction import DREBINFeatureExtractor
import logging


class BaseDREBIN(BaseModel):
    """
    Base class for any scikit-learn or secml classifier that can be trained on
    the DREBIN feature set.
    Features are parsed with a CountVectorizer, supporting both sparse and
    dense formats.
    It must be extended by implementing the _fit and predict methods.
    method.
    """

    def __init__(self):
        self._vectorizer = CountVectorizer(
            input="content", lowercase=False,
            tokenizer=lambda x: x, binary=True, token_pattern=None)
        self._feat_extractor = DREBINFeatureExtractor(
            logging_level=logging.ERROR)
        self._input_features = None

    def fit(self, features, y):
        """

        Parameters
        ----------
        features: iterable of iterables of strings
            Iterable of shape (n_samples, n_features) containing textual
            features in the format <feature_type>::<feature_name>.
        y : np.ndarray
            Array of shape (n_samples,) containing the class labels.
        """
        X = self._vectorizer.fit_transform(features)
        self._input_features = (self._vectorizer.get_feature_names_out()
                                .tolist())
        self._fit(X, y)

    def _fit(self, X, y):
        """

        Parameters
        ----------
        X: scipy sparse matrix
            Sparse matrix of shape (n_samples, n_features) containing the
            features.
        y : np.ndarray
            Array of shape (n_samples,) containing the class labels.
        """
        return NotImplemented

    def extract_features(self, apk_list):
        """

        Parameters
        ----------
        apk_list : list of str
            List with the absolute path of each APK file to classify.

        Returns
        -------
        iterable of iterables of strings
            Iterable of shape (n_samples, n_features) containing textual
            features in the format <feature_type>::<feature_name>.
        """
        return self._feat_extractor.extract_features(apk_list)

    def classify(self, apk_list):
        features = self.extract_features(apk_list)
        return self.predict(features)

    def save(self, vectorizer_path, classifier_path):
        """

        Parameters
        ----------
        vectorizer_path : str
        classifier_path : str
        """
        with open(vectorizer_path, "wb") as f:
            pkl.dump(self._vectorizer, f)
        vectorizer = self._vectorizer
        self._vectorizer = None
        with open(classifier_path, "wb") as f:
            pkl.dump(self, f)
        self._vectorizer = vectorizer

    @staticmethod
    def load(vectorizer_path, classifier_path):
        """

        Parameters
        ----------
        vectorizer_path : str
        classifier_path : str

        Returns
        -------
        BaseDREBIN
        """
        with open(classifier_path, "rb") as f:
            classifier = pkl.load(f)
        with open(vectorizer_path, "rb") as f:
            classifier._vectorizer = pkl.load(f)
        return classifier

    @property
    def input_features(self):
        return self._input_features
