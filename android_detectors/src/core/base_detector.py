from abc import ABC, abstractmethod
from core import HostFilePath


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
        labels: list[int],
        *args,
        **kwargs
    ):
        """
        Train the model on the given APKs.
        Each detector may specify it own parameters.

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
        Each detector may specify it own parameters.

        Parameters
        ----------
        apk_paths: list[str]
            The path of the APK files to be classified.
            If the detector is containerized, you can pass the path on the
            host, and the files will be automatically make available with RO
            access to the container thanks to the HostFilePath type annotation.
            Otherwise, the path will be kept unaltered.
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, *args, **kwargs):
        """
        Save a detector into one or more files.
        Each detector may specify it own parameters.
        If the detector is containerized, the files can only be saved under
        the `data/{detector_name}` host folder inside this project's root, as
        the container has RW access to it. In this case, you must type the
        paths with the `ContainerFilePath` special type included in
        `core.types`.
        """
        raise NotImplementedError

    @abstractmethod
    def load(self, *args, **kwargs):
        """
        Load a detector from one or more files.
        Each detector may specify it own parameters.
        If the detector is containerized, the files can only be loaded under
        the `data/{detector_name}` host folder inside this project's root, as
        the container has RW access to it. In this case, you must type the
        paths with the `ContainerFilePath` special type included in
        `core.types`.
        """
        raise NotImplementedError
