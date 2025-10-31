from abc import ABC, abstractmethod
from core.types import *


class BaseDetector(ABC):
    """
    Abstract base class that defines the mandatory interface for all ML
    detectors.

    Concrete implementations must subclass this class, and can add their
    specific parameters to each method.
    """

    @abstractmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def train(
        self,
        apk_paths: list[HostFilePath],
        *args,
        **kwargs
    ):
        """
        Train the model on the given APKs.

        Parameters
        ----------
        apk_paths: list[str]
            The path of the APK files to be used for training the model.
            If the detector is containerized, you can pass the path on the
            host, and the files will be automatically make available with RO
            access to the container thanks to the HostFilePath type annotation.

        """
        raise NotImplementedError

    @abstractmethod
    def classify(
        self,
        apk_paths: list[HostFilePath],
        *args,
        **kwargs
    ) -> tuple[list[int], list[float]]:
        """
        Run inference/classification on the given APKs.

        """
        raise NotImplementedError

    @abstractmethod
    def save(self, *args, **kwargs):
        """
        Save a detector into a container path.

        Parameters
        ----------

        """
        raise NotImplementedError

    @abstractmethod
    def load(self, *args, **kwargs):
        """
        Load a detector from a container path.

        Parameters
        ----------

        """
        raise NotImplementedError
