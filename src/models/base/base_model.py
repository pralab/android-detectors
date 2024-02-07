class BaseModel:
    """
    Interface for models to be submitted in the ELSA Cybersecurity benchmark.

    - Track 1 - Adversarial Robustness to Feature-space Attacks
      Requested Methods/Properties: predict, input_features

    - Track 2: Adversarial Robustness to Problem-space Attacks
      Requested Methods: classify

    - Track 3: Temporal Robustness to Data Drift
      Requested Methods: classify
    """

    def predict(self, features):
        """
        Given the textual features of the samples to classify, returns the
        predicted labels and scores.

        Parameters
        ----------
        features: iterable of iterables of strings
            Iterable of shape (n_samples, n_features) containing textual
            features in the format <feature_type>::<feature_name>.

        Returns
        -------
        labels : numpy.ndarray
            Flat dense array of shape (n_samples,) with the label assigned
            to each test pattern. The classification label is the label of
            the class associated with the highest score.
        scores : numpy.ndarray
            Array of shape (n_samples,) with classification
            score of each test pattern with respect to the positive class.
        """
        return NotImplemented

    @property
    def input_features(self):
        """

        Returns
        -------
        features : list of str
            List with the name of input features used by the model, in the
            format <feature_type>::<feature_name>.
        """
        return NotImplemented

    def classify(self, apk_list):
        """
        Given a list of APK file paths, extracts the features and classifies
        them, returning the predicted labels and scores.

        Parameters
        ----------
        apk_list : list of str
            List with the absolute path of each APK file to classify.

        Returns
        -------
        labels : numpy.ndarray
            Flat dense array of shape (n_samples,) with the label assigned
            to each test pattern. The classification label is the label of
            the class associated with the highest score.
        scores : numpy.ndarray
            Array of shape (n_samples,) with classification
            score of each test pattern with respect to the positive class.
        """
        return NotImplemented
