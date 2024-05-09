from utils.multiprocessing import killer_pmap


class BaseFeatureExtractor:

    def __init__(self):
        self._features_out_dir = None

    def extract_features(self, apk_list, timeout=600, out_dir=None):
        """

        Parameters
        ----------
        apk_list : list of str
            List with the absolute path of each APK file from which to extract
            the features.
        timeout : int
            Maximum allowed time in seconds for processing each APK file. Must
            be greater than 10. If the timeout is exceeded, the feature
            extraction for that file is skipped, and the filename is appended
            to `apks_not_processed.txt`.
        out_dir : str or None
            If provided, the extracted features are saved in this directory.
        Returns
        -------
        iterable
            An iterable containing the extracted features.
        """

        if not isinstance(timeout, int):
            raise ValueError("the timeout variable must be an Integer")
        elif timeout < 10:
            raise ValueError("the timeout variable must be greater than 10sec")

        self._features_out_dir = out_dir

        return killer_pmap(self._extract_features, apk_list, timeout=timeout)

    def _extract_features(self, apk):
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
