from feature_extraction.base_feature_extractor import BaseFeatureExtractor
from feature_extraction.drebin.apk_analyzer import process_apk
import logging
import os
import json


class DREBINFeatureExtractor(BaseFeatureExtractor):
    """
    Implements (addressing as many updates as possible) the feature extractor
    from:
      Arp, Daniel, et al. "Drebin: Effective and explainable detection of
      android malware in your pocket." NDSS 2014.
      https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf
    """

    def __init__(self, logging_level=logging.INFO):
        """

        Parameters
        ----------
        logging_level : int
            Set the verbosity of the logger.
        """
        super(DREBINFeatureExtractor, self).__init__()
        self._set_logger(logging_level)

    def _extract_features(self, apk):
        if self._features_out_dir is not None:
            file_name = os.path.join(
                self._features_out_dir,
                os.path.splitext(os.path.basename(apk))[0] + ".json")
            if os.path.exists(file_name):
                self.logger.info(f"feature for {apk} were already extracted")
                with open(file_name, "r") as js:
                    data = json.load(js)
                    return [f"{k}::{v}" for k in data
                            for v in data[k] if data[k]]
        if os.path.exists(apk) and os.path.getsize(apk) > 0:
            result = process_apk(apk, self._features_out_dir, self.logger)
            self.logger.info(f"{apk} features were successfully extracted")
            return result
        else:
            self.logger.error(f"{apk} does not exist or is an empty file")
        return None

    def _set_logger(self, logging_level):
        logging.basicConfig(
            level=logging_level, filename="apk_analysis.log", filemode="a",
            format="%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: "
                   "%(message)s", datefmt="%Y/%m/%d %H:%M:%S")
        error_handler = logging.StreamHandler()
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            logging.Formatter("%(asctime)s %(filename)s[line:%(lineno)d] "
                              "%(levelname)s: %(message)s"))
        self.logger = logging.getLogger()
        self.logger.addHandler(error_handler)
        logging.getLogger("androguard.dvm").setLevel(logging.CRITICAL)
        logging.getLogger("androguard.core.api_specific_resources").setLevel(
            logging.CRITICAL)
        logging.getLogger("androguard.axml").setLevel(logging.CRITICAL)
        logging.getLogger("androguard.apk").setLevel(logging.CRITICAL)
