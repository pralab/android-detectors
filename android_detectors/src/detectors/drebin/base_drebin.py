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
from pathlib import Path
from typing import Generator, Iterable


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

    def train(
        self,
        apk_paths: list[HostFilePath] | None = None,
        labels: list[int] | None = None,
        features_zip: ContainerFilePath | None = None,
        dataset_file_zip: ContainerFilePath | None = None,
    ):
        """
        Trains the model on the given data. It accepts either a list of APK file
        paths and their corresponding labels, or the compressed features and
        dataset metadata files.

        Parameters
        ----------
        apk_paths: list[str]
            The path of the APK files to be used for training the model.
            If the detector is containerized, you can pass the path on the
            host, and the files will be automatically make available with RO
            access to the container thanks to the HostFilePath type annotation.
            Otherwise, the path will be kept unaltered.
        labels: list[int]
            The ground-truth binary labels corresponding to each training set
            sample.
        features_zip: str
            The path of the compressed pre-extracted features.
            If the detector is containerized, it must be inside the
            `data/{detector_name}` project folder o a subfolder thereof.
        dataset_file_zip: str
            The path of the compressed dataset metadata file.
            If the detector is containerized, it must be inside the
            `data/{detector_name}` project folder o a subfolder thereof.
        """
        if features_zip is not None and dataset_file_zip is not None:
            features = self._load_features_zip(features_zip)
            labels = self._load_labels(features_zip, dataset_file_zip)
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
        """Private train method that accepts the vectorized features and
        the labels array, which will be passed to the classifier.

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
        """
        Given the textual extracted features, returns the predicted labels
        and scores.

        Parameters
        ----------
        features: list[str]
            The textual features in the format <feature_type>::<feature_name>.

        Returns
        -------
        tuple[list[int], list[float]]
            The predicted labels and scores.
        """
        pass

    def extract_features(
        self,
        apk_list: list[HostFilePath]
    ) -> Iterable[list[str]]:
        """
        Given a list of APK file paths, extracts their features and returns them.

        Parameters
        ----------
        apk_list : list[str]
            The path of the APKs from which to extract the features.
            If the detector is containerized, you can pass the path on the
            host, and the files will be automatically make available with RO
            access to the container thanks to the HostFilePath type annotation.
            Otherwise, the path will be kept unaltered.

        Returns
        -------
        Iterable[list[str]]
            Iterable of shape (n_samples, n_features) containing for each sample
            a list with the textual features in the format
            <feature_type>::<feature_name>.
        """
        return self._feat_extractor.extract_features(apk_list)

    def classify(
        self,
        apk_paths: list[HostFilePath] | None = None,
        features_zip: ContainerFilePath | None = None
    ) -> tuple[list[int], list[float]]:
        """
        Given a list of APK file paths, returns the predicted labels
        and scores.

        Parameters
        ----------
        apk_paths : list[str]
            The path of the APKs from which to extract the features.
            If the detector is containerized, you can pass the path on the
            host, and the files will be automatically make available with RO
            access to the container thanks to the HostFilePath type annotation.
            Otherwise, the path will be kept unaltered.

        Returns
        -------
        tuple[list[int], list[float]]
            The predicted labels and scores.
        """
        if apk_paths is not None:
            features = self.extract_features(apk_paths)
        elif features_zip is not None:
            features = self._load_features_zip(features_zip)
        else:
            raise ValueError(
                "You must provide either `apk_paths` or `features_zip`")
        return self.predict(features)

    def save(
        self,
        classifier_path: ContainerFilePath,
        vectorizer_path: ContainerFilePath,
    ) -> None:
        """
        Save the detector.

        Parameters
        ----------
        classifier_path : str
            The path where to store the classifier.
            If the detector is containerized, it must be inside the
            `data/{detector_name}` project folder o a subfolder thereof.
        vectorizer_path : str
            The path where to store the vectorizer.
            If the detector is containerized, it must be inside the
            `data/{detector_name}` project folder o a subfolder thereof.
        """
        with open(vectorizer_path, "wb") as f:
            pkl.dump(self._vectorizer, f)
        vectorizer = self._vectorizer
        self._vectorizer = None
        with open(classifier_path, "wb") as f:
            pkl.dump(self, f)
        self._vectorizer = vectorizer

    def load(
        self,
        classifier_path: ContainerFilePath,
        vectorizer_path: ContainerFilePath,
    ) -> None:
        """
        Load the detector.

        Parameters
        ----------
        classifier_path : str
            The path from where to load the classifier.
            If the detector is containerized, it must be inside the
            `data/{detector_name}` project folder o a subfolder thereof.
        vectorizer_path : str
            The path from where to load the vectorizer.
            If the detector is containerized, it must be inside the
            `data/{detector_name}` project folder o a subfolder thereof.
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
    def _load_features_zip(
        features_path: str
    ) -> Generator[list[str], None, None]:
        """
        Load the pre-extracted features from the JSON files contained in a
        compressed zip.

        Parameters
        ----------
        features_path : str
            Absolute path of the features compressed file.

        Returns
        -------
        Generator[list[str]]
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
    def _load_labels(
        features_path: str,
        ds_data_path: str
    ) -> list[int]:
        """
        Load the labels from the dataset metadata compressed CSV file,
        corresponding to the pre-extracted features contained in the feature
        compressed zip.

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
            List containing the class labels.
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
