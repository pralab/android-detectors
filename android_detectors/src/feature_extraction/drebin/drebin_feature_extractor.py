"""Implementation of the DREBIN feature extractor."""

import json
import logging
from pathlib import Path

import ray

from feature_extraction.base_feature_extractor import BaseFeatureExtractor
from feature_extraction.drebin.apk_analyzer import process_apk


class DREBINFeatureExtractor(BaseFeatureExtractor):
    """
    Implements (addressing as many updates as possible) the feature extractor
    from:
      Arp, Daniel, et al. "Drebin: Effective and explainable detection of
      android malware in your pocket." NDSS 2014.
      https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf
    """  # noqa: D400

    def __init__(self, logging_level: int = logging.INFO) -> None:
        """
        Create and initialize the DREBIN feature extractor.

        Parameters
        ----------
        logging_level : int
            Set the verbosity of the logger.
        """
        super(__class__, self).__init__()
        self._set_logger(logging_level)

    @ray.remote
    def _extract_features(self, apk: str) -> list[str] | None:
        sha256 = self._get_hash(apk)
        if self._features_out_dir is not None:
            file_name = Path(self._features_out_dir) / f"{sha256}.json"
            if Path(file_name).is_file():
                self.logger.info("Feature for %s were already extracted", apk)
                return self._load_features(features_file=file_name)

        if Path(apk).is_file() and Path(apk).stat().st_size > 0:
            result = process_apk(apk, sha256, self._features_out_dir, self.logger)
            self.logger.info("%s features were successfully extracted", apk)
            return result

        self.logger.error("%s does not exist or is an empty file", apk)
        return None

    @staticmethod
    def _load_features(js: dict = None, features_file: str | Path = None):
        if js is None:
            with open(features_file, "r") as f:
                js = json.load(f)
        return [f"{k}::{v}" for k in js for v in js[k] if js[k]]

    def _set_logger(self, logging_level: int) -> None:
        logging.basicConfig(
            level=logging_level,
            filename="apk_analysis.log",
            filemode="a",
            format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: "
            "%(message)s",
            datefmt="%Y/%m/%d %H:%M:%S",
        )
        error_handler = logging.StreamHandler()
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s"
            )
        )
        self.logger = logging.getLogger()
        self.logger.addHandler(error_handler)
        logging.getLogger("androguard.dvm").setLevel(logging.CRITICAL)
        logging.getLogger("androguard.core.api_specific_resources").setLevel(
            logging.CRITICAL
        )
        logging.getLogger("androguard.axml").setLevel(logging.CRITICAL)
        logging.getLogger("androguard.apk").setLevel(logging.CRITICAL)
