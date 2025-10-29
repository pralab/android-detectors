from core.detector_interface import DetectorInterface
from .pydantic_models import *
from abc import ABC, abstractmethod
from sklearn.feature_extraction.text import CountVectorizer
import dill as pkl
import json
import pandas as pd
from zipfile import ZipFile, ZIP_DEFLATED
from feature_extraction import DREBINFeatureExtractor
import logging


def tkn(x):
    return x


class BaseDREBIN(DetectorInterface, ABC):
    """
    Base class for any scikit-learn or secml classifier that can be trained on
    the DREBIN feature set.
    Features are parsed with a CountVectorizer, supporting both sparse and
    dense formats.
    It must be extended by implementing the _fit and predict methods.
    method.
    """

    def __init__(
        self,
        init_args: BaseInit,
    ) -> None:
        self._vectorizer = CountVectorizer(
            input="content", lowercase=False,
            tokenizer=tkn, binary=True, token_pattern=None)
        self._feat_extractor = DREBINFeatureExtractor(
            logging_level=logging.ERROR)
        self._input_features = None

    def train(
        self,
        train_args: DrebinTrain,
    ) -> BaseTrainResponse:
        if train_args.apk_paths is None:
            features = self._load_features_zip(train_args.features_zip)
            labels = self._load_labels(train_args.features_zip,
                                       train_args.dataset_file_zip)
        else:
            features = self.extract_features(train_args.apk_paths)
            filtered = [(feat, label) for feat, label in
                        zip(features, train_args.labels) if feat is not None]
            if not filtered:
                raise ValueError("There are no valid extracted features.")
            features, labels = zip(*filtered)
        X = self._vectorizer.fit_transform(features)
        self._input_features = (self._vectorizer.get_feature_names_out()
                                .tolist())
        self._train(X, labels)
        return BaseTrainResponse()

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
    def predict(self, features):
        pass

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

    def classify(
        self,
        classify_args: DrebinClassify,
    ) -> BaseClassifyResponse:
        if classify_args.apk_paths is not None:
            features = self.extract_features(classify_args.apk_paths)
        else:
            features = self._load_features_zip(classify_args.features_zip)
        return self.predict(features)

    def save(
        self,
        save_args: DrebinSaveLoad,
    ) -> None:
        """

        Parameters
        ----------
        """
        with open(save_args.vectorizer_path, "wb") as f:
            pkl.dump(self._vectorizer, f)
        vectorizer = self._vectorizer
        self._vectorizer = None
        with open(save_args.path, "wb") as f:
            pkl.dump(self, f)
        self._vectorizer = vectorizer

    def load(
        self,
        load_args: DrebinSaveLoad,
    ) -> None:
        """

        Parameters
        ----------

        Returns
        -------
        BaseDREBIN
        """
        with open(load_args.path, "rb") as f:
            classifier = pkl.load(f)
            self.__dict__.update(classifier.__dict__)
        with open(load_args.vectorizer_path, "rb") as f:
            self._vectorizer = pkl.load(f)
            self._vectorizer.tokenizer = tkn

    @property
    def input_features(self):
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
        with ZipFile(ds_data_path, "r", ZIP_DEFLATED) as z:
            ds_csv = pd.concat(
                [pd.read_csv(z.open(f))[["sha256", "label"]]
                 for f in z.namelist()], ignore_index=True)
            labels_json = {k: v for k, v in zip(ds_csv.sha256.values,
                                                    ds_csv.label.values)}

        with ZipFile(features_path, "r", ZIP_DEFLATED) as z:
            labels = [labels_json[f.split(".json")[0].lower()]
                      for f in z.namelist()]
        return labels
