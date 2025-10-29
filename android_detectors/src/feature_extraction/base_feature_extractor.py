"""Implementation of the Android base feature extractor class."""

from typing import Optional

import hashlib
import ray


class BaseFeatureExtractor:
    """Base class for Android feature extractors."""

    def __init__(self) -> None:
        """Create and initialize the feature extractor."""
        self._features_out_dir = None

    def extract_features(
        self, apk_list: list[str], out_dir: Optional[str] = None
    ) -> list[list[str]]:
        """
        Extract features from a list of APK files.

        Parameters
        ----------
        apk_list : list[str]
            List with the absolute path of each APK file from which to extract
        out_dir : str or None
            If provided, the extracted features are saved in this directory.

        Returns
        -------
        list[list[str]]
            A list containing the extracted features for each APK file.
        """
        self._features_out_dir = out_dir

        return ray.get([self._extract_features.remote(self, apk) for apk in apk_list])

    @ray.remote
    def _extract_features(self, apk: str) -> list[str] | None:
        """

        Parameters
        ----------
        apk : str
            Absolute path of the APK file to analyze.

        Returns
        -------
        The extracted features for the provided APK file, or None if the
        operation fails.
        """
        return NotImplemented

    @staticmethod
    def _get_hash(file_path):
        with open(file_path, mode='rb') as f:
            bytes = f.read()
            sha256_hash = hashlib.sha256(bytes).hexdigest().upper()
        return sha256_hash
