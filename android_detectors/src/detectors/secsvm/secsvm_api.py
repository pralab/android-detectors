# Auto-generated stub.
from pydantic import validate_call
from core.dockerized_detector import DockerizedDetector
from core.types import *


class SecSVM(DockerizedDetector):
    """Secure Support Vector Machine (Sec-SVM) classifier.

    This implements the secure classifier from:

     Demontis et al. "Yes, machine learning can be more secure! a case study
     on android malware detection." IEEE TDSC 2017. https://arxiv.org/abs/1704.08996

    Parameters
    ----------
    C : float, optional
        Penalty hyper-parameter C of the error term. Default 1.0.
    kernel : None or CKernel subclass, optional
        Instance of a CKernel subclass to be used for computing
        similarity between patterns. If None (default), a linear
        SVM is trained in the primal; otherwise an SVM is trained in the dual,
        using the precomputed kernel values.
    class_weight : {dict, 'balanced', None}, optional
        Set the parameter C of class i to `class_weight[i] * C`.
        If not given (default), all classes are supposed to have
        weight one. The 'balanced' mode uses the values of labels to
        automatically adjust weights inversely proportional to
        class frequencies as `n_samples / (n_classes * np.bincount(y))`.
    ub : scalar or None, optional
        Upper bound of the weights. If None (default), no bound is applied.
    idx_ub : CArray or None, optional
        If CArray, the upper bound is only applied to the weights indicized
        by `idx_ub`. If None (default), the bound is applied to all weights.
    lb : scalar or None, optional
        Lower bound of the weights. If None (default), no bound is applied.
    idx_lb : CArray or None, optional
        If CArray, the lower bound is only applied to the weights indicized
        by `idx_ub`. If None (default), the bound is applied to all weights.
    eta : scalar, optional
        Step of the gradient descent. Default 0.5.
    max_it : int, optional
        Maximum number of iterations of the gradient descent. Default 1e4.
    eps : scalar, optional
        Tolerance of the stop criterion of the gradient descent. Default 1e-4.
    """
    name = "sec_svm"
    implementation_module = "secsvm"
    implementation_class = "SecSVM"
    image_tag = "sec_svm:latest"

    def __init__(self, C=0.1, kernel=None, class_weight=None, ub=inf, idx_ub=None, lb=-inf, idx_lb=None, eta=0.5, max_it=10000.0, eps=0.0001):
        super().__init__(C, kernel, class_weight, ub, idx_ub, lb, idx_lb, eta, max_it, eps)

    @validate_call
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

    @validate_call
    def load(self, classifier_path: ContainerFilePath, vectorizer_path: ContainerFilePath) -> None:
        """

        Parameters
        ----------

        Returns
        -------
        BaseDREBIN
        """
        return super().load(classifier_path, vectorizer_path)

    @validate_call
    def save(self, classifier_path: ContainerFilePath, vectorizer_path: ContainerFilePath) -> None:
        """

        Parameters
        ----------
        """
        return super().save(classifier_path, vectorizer_path)

    @validate_call(validate_return=True)
    def classify(self, apk_paths: list[HostFilePath] | None=None, features_zip: ContainerFilePath | None=None) -> tuple[list[int], list[float]]:
        return super().classify(apk_paths, features_zip)
