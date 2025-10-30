from pathlib import Path
import tempfile


# data folders
PROJECT_ROOT = Path(__file__).parent.parent
HOST_SHARED_RW_DATA = PROJECT_ROOT.parent / "data"
HOST_SHARED_RO_DATA = Path(tempfile.gettempdir()) / "android-detectors_shared"
CONTAINER_SHARED_RW_DATA = "/data"
CONTAINER_SHARED_RO_DATA = "/shared"

# environment variables
DOCKERIZED = "DOCKERIZED"
RUNNING_IN_CONTAINER = "RUNNING_IN_CONTAINER"
DETECTOR_CLASS = "DETECTOR_CLASS"

# methods that must be exposed by each detector
DETECTOR_INTERFACE = {"__init__", "train", "classify", "save", "load"}
