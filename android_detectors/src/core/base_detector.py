from abc import ABC, abstractmethod
from core.types import *


class BaseDetector(ABC):
    """
    Abstract base class that defines the mandatory interface for all ML
    detectors.

    Concrete implementations (that will run inside containers) must subclass
    this class. The host-side `RemoteDetector` also inherits this class to
    satisfy static type checkers and provide a consistent API to the main
    program.
    """

    @abstractmethod
    def __init__(self, *args, **kwargs):
        """
        Construct a model with model-specific keyword arguments.

        Parameters
        ----------
        """
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
