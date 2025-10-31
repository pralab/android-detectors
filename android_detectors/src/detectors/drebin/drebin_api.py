# Auto-generated stub.
from core.dockerized_detector import DockerizedDetector
from core.types import *


class DREBIN(DockerizedDetector):
    """
    Implements the DREBIN classifier from:
      Arp, Daniel, et al. "Drebin: Effective and explainable detection of
      android malware in your pocket." NDSS 2014.
      https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf
    """
    name = "drebin"
    implementation_module = "drebin"
    implementation_class = "DREBIN"
    image_tag = "drebin:latest"

    def __init__(self, tol: float=0.0001, C: float=0.1, class_weight: dict | str | None=None, verbose: int=0, random_state: int=0, max_iter: int=1000):
        """

        Parameters
        ----------
        tol : float, default=1e-4
            Tolerance for stopping criteria.
        C : float, default=0.1
            Regularization parameter. The strength of the regularization is
            inversely proportional to C. Must be strictly positive.
        class_weight : dict or 'balanced', default=None
            Set the parameter C of class i to ``class_weight[i]*C`` for
            SVC. If not given, all classes are supposed to have
            weight one.
            The "balanced" mode uses the values of y to automatically adjust
            weights inversely proportional to class frequencies in the input data
            as ``n_samples / (n_classes * np.bincount(y))``.
        verbose : int, default=0
            Enable verbose output. Note that this setting takes advantage of a
            per-process runtime setting in liblinear that, if enabled, may not work
            properly in a multithreaded context.
        random_state : int, RandomState instance or None, default=None
            Controls the pseudo random number generation for shuffling the data for
            the dual coordinate descent (if ``dual=True``). When ``dual=False`` the
            underlying implementation of :class:`LinearSVC` is not random and
            ``random_state`` has no effect on the results.
            Pass an int for reproducible output across multiple function calls.
            See :term:`Glossary <random_state>`.
        max_iter : int, default=1000
            The maximum number of iterations to be run.
        """
        super().__init__(tol, C, class_weight, verbose, random_state, max_iter)

    def train(self, apk_paths: list[HostFilePath] | None=None, labels: list[int] | None=None, features_zip: ContainerFilePath | None=None, dataset_file_zip: ContainerFilePath | None=None):
        """
        Parameters
        ----------
        apk_paths
        labels
        features_zip
        dataset_file_zip
        """
        return super().train(apk_paths, labels, features_zip, dataset_file_zip)

    def load(self, classifier_path: ContainerFilePath, vectorizer_path: ContainerFilePath) -> None:
        """

        Parameters
        ----------

        Returns
        -------
        BaseDREBIN
        """
        return super().load(classifier_path, vectorizer_path)

    def save(self, classifier_path: ContainerFilePath, vectorizer_path: ContainerFilePath) -> None:
        """

        Parameters
        ----------
        """
        return super().save(classifier_path, vectorizer_path)

    def classify(self, apk_paths: list[HostFilePath] | None=None, features_zip: ContainerFilePath | None=None) -> tuple[list[int], list[float]]:
        return super().classify(apk_paths, features_zip)
