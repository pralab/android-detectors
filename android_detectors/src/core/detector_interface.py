from abc import ABC, abstractmethod
from core.pydantic_models import *


class DetectorInterface(ABC):
    """
    Abstract base class that defines the mandatory interface for all ML
    detectors.

    Concrete implementations (that will run inside containers) must subclass
    this class. The host-side `RemoteDetector` also inherits this class to
    satisfy static type checkers and provide a consistent API to the main
    program.
    """

    @abstractmethod
    def __init__(
        self,
        init_args: BaseInit,
    ) -> None:
        """
        Construct a model with model-specific keyword arguments.

        Parameters
        ----------
        init_args : BaseInit
            Pydantic model containing all the init arguments
            (empty by default). Each detector may specify its own arguments
            by defining a new Pydantic model subclassing BaseInit.
        """
        raise NotImplementedError

    @abstractmethod
    def train(
        self,
        train_args: BaseTrain,
    ) -> BaseTrainResponse:
        """
        Train the model on the given APKs.

        Parameters
        ----------
        train_args : BaseTrain
            Pydantic model containing all the training arguments.
            By default, it requires:
                - apk_paths : list[str]
                    List with the absolute path of each training APK file.
                - labels : list[int]
                    List containing the binary class labels (either 0 or 1).
            Each detector may specify additional arguments by defining a new
            Pydantic model subclassing BaseTrain.

        Returns
        -------
        BaseTrainResponse
            Pydantic model containing metadata about the training outcome.
            By default, it is empty. Each detector may specify custom fields
            by defining a new Pydantic model subclassing BaseTrainResponse.
        """
        raise NotImplementedError

    @abstractmethod
    def classify(
        self,
        classify_args: BaseClassify,
    ) -> BaseClassifyResponse:
        """
        Run inference/classification on the given APKs.

        Parameters
        ----------
        classify_args : BaseClassify
            Pydantic model containing all the inference arguments.
            By default, it requires:
                - apk_paths : list[str]
                    List with the absolute path of each APK file to classify.
            Each detector may specify additional arguments by defining a new
            Pydantic model subclassing BaseClassify.

        Returns
        -------
        BaseClassifyResponse
            Pydantic model containing the classification outputs.
            By default, it contains:
                - labels : list[int]
                    List containing the binary the label (either 0 or 1)
                    assigned to each test pattern. The classification label is
                    the label of the class associated with the highest score.
                - scores : list[float]
                    List containing the classification score of each test
                    pattern with respect to the positive class.
            Each detector may specify additional fields by defining a new
            Pydantic model subclassing BaseClassifyResponse.

        """
        raise NotImplementedError

    @abstractmethod
    def save(
        self,
        save_args: BaseSave,
    ) -> None:
        """
        Save a detector into a container path.

        Parameters
        ----------
        save_args : BaseSave
            Pydantic model containing all the arguments needed to save the
            detector state.
            By default, it requires:
                - path : str
                    Absolute path where to save the detector.
            Each detector may specify additional arguments by defining a new
            Pydantic model subclassing BaseSave.

        """
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def load(
        load_args: BaseLoad,
    ) -> "DetectorInterface":
        """
        Load a detector from a container path.

        Parameters
        ----------
        load_args : BaseLoad
            Pydantic model containing all the arguments needed to load the
            detector state.
            By default, it requires:
                - path : str
                    Absolute path from where to load the detector.
            Each detector may specify additional arguments by defining a new
            Pydantic model subclassing BaseLoad.

        Returns
        -------
        DetectorInterface
            The instantiated detector.
        """
        raise NotImplementedError
