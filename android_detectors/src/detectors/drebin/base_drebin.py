from core.base_detector import BaseDetector
from core.types import *
from abc import ABC, abstractmethod
from sklearn.feature_extraction.text import CountVectorizer
import dill as pkl
import json
import pandas as pd
from zipfile import ZipFile, ZIP_DEFLATED
from feature_extraction import DREBINFeatureExtractor
import logging
from pydantic import validate_call
from pathlib import Path


def tkn(x):
    return x


class BaseDREBIN(BaseDetector, ABC):
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
            tokenizer=tkn, binary=True, token_pattern=None)
        self._feat_extractor = DREBINFeatureExtractor(
            logging_level=logging.ERROR)
        self._input_features = None

    @validate_call
    def train(
        self,
        apk_paths: list[HostFilePath] | None = None,
        labels: list[int] | None = None,
        features_zip: ContainerFilePath | None = None,
        dataset_file_zip: ContainerFilePath | None = None,
    ):
        """
        Parameters
        ----------
        apk_paths
        labels
        features_zip
        dataset_file_zip
        """
        if features_zip is not None and dataset_file_zip is not None:
            features = self._load_features_zip(features_zip)
            labels = self._load_labels(features_zip,
                                       dataset_file_zip)
        elif apk_paths is not None and labels is not None:
            features = self.extract_features(apk_paths)
            filtered = [(feat, label) for feat, label in
                        zip(features, labels) if feat is not None]
            if not filtered:
                raise ValueError("There are no valid extracted features.")
            features, labels = zip(*filtered)
        else:
            raise ValueError(
                "You must either provide `apk_paths` and `labels` or"
                "`features_zip` and `dataset_file_zip`")
        X = self._vectorizer.fit_transform(features)
        self._input_features = (self._vectorizer.get_feature_names_out()
                                .tolist())
        self._train(X, labels)

    @abstractmethod
    def _train(self, X, y):
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

    @abstractmethod
    def predict(
        self,
        features: list[str]
    ) -> tuple[list[int], list[float]]:
        pass

    @validate_call
    def extract_features(
        self,
        apk_list: list[HostFilePath]
    ):
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

    @validate_call(validate_return=True)
    def classify(
        self,
        apk_paths: list[HostFilePath] | None = None,
        features_zip: ContainerFilePath | None = None
    ) -> tuple[list[int], list[float]]:
        if apk_paths is not None:
            features = self.extract_features(apk_paths)
        elif features_zip is not None:
            features = self._load_features_zip(features_zip)
        else:
            raise ValueError(
                "You must provide either `apk_paths` or `features_zip`")
        return self.predict(features)

    @validate_call
    def save(
        self,
        classifier_path: ContainerFilePath,
        vectorizer_path: ContainerFilePath,
    ) -> None:
        """

        Parameters
        ----------
        """
        with open(vectorizer_path, "wb") as f:
            pkl.dump(self._vectorizer, f)
        vectorizer = self._vectorizer
        self._vectorizer = None
        with open(classifier_path, "wb") as f:
            pkl.dump(self, f)
        self._vectorizer = vectorizer

    @validate_call
    def load(
        self,
        classifier_path: ContainerFilePath,
        vectorizer_path: ContainerFilePath,
    ) -> None:
        """

        Parameters
        ----------

        Returns
        -------
        BaseDREBIN
        """
        with open(classifier_path, "rb") as f:
            classifier = pkl.load(f)
            self.__dict__.update(classifier.__dict__)
        with open(vectorizer_path, "rb") as f:
            self._vectorizer = pkl.load(f)
            self._vectorizer.tokenizer = tkn

    @property
    def input_features(self) -> list[str]:
        return self._input_features

    @staticmethod
    def _load_features_zip(features_path: str):
        """

        Parameters
        ----------
        features_path :
            Absolute path of the features compressed file.

        Returns
        -------
        generator of list of strings
            Iteratively returns the textual feature vector of each sample.
        """
        if not Path(features_path).is_file():
            raise FileNotFoundError(f"The file `{features_path}` does not exist!")
        with ZipFile(features_path, "r", ZIP_DEFLATED) as z:
            for filename in z.namelist():
                with z.open(filename) as fp:
                    js = json.load(fp)
                    yield [f"{k}::{v}" for k in js for v in js[k] if js[k]]

    @staticmethod
    def _load_labels(features_path: str, ds_data_path: str):
        """

        Parameters
        ----------
        features_path : str
            Absolute path of the features compressed file.
        ds_data_path : str
            Absolute path of the dataset file (compressed csv) containing
            the labels.

        Returns
        -------
        list[int]
            List of shape (n_samples,) containing the class labels.
        """
        if not Path(ds_data_path).is_file():
            raise FileNotFoundError(f"The file `{ds_data_path}` does not exist!")
        with ZipFile(ds_data_path, "r", ZIP_DEFLATED) as z:
            ds_csv = pd.concat(
                [pd.read_csv(z.open(f))[["sha256", "label"]]
                 for f in z.namelist()], ignore_index=True)
            labels_json = {k: v for k, v in zip(ds_csv.sha256.values,
                                                    ds_csv.label.values)}

        if not Path(features_path).is_file():
            raise FileNotFoundError(f"The file `{features_path}` does not exist!")
        with ZipFile(features_path, "r", ZIP_DEFLATED) as z:
            labels = [labels_json[f.split(".json")[0].lower()]
                      for f in z.namelist()]
        return labels
