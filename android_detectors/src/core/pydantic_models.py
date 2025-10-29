from pydantic import BaseModel, AfterValidator
from pathlib import Path
from typing import Annotated
import tempfile
import os


__all__ = [
    "HostFilePath", "ContainerFilePath", "BaseInit", "BaseTrain",
    "BaseTrainResponse", "BaseClassify", "BaseClassifyResponse", "BaseSave",
    "BaseLoad", "OkResponse", "HealthResponse"
]


def _link_host_file(
    path: str,
) -> str:
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f"File {path} does not exist")
    if os.getenv("RUNNING_IN_DETECTOR_CONTAINER") == "1":
        return str(path)
    tmp_data_dir = Path(
        tempfile.gettempdir()) / "android-detectors_shared"
    dest = tmp_data_dir / path.relative_to(path.anchor)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        dest.hardlink_to(path)
    except FileExistsError:
        pass
    return str(Path("/shared") / path.relative_to(path.anchor))


def _host_to_container_path(
    path: str,
) -> str:
    path = Path(path).resolve()
    if os.getenv("RUNNING_IN_DETECTOR_CONTAINER") == "1":
        return str(path)
    try:
        data_path = Path(__file__).parent.parent.parent.parent / "data"
        data_path.mkdir(exist_ok=True)
        path = path.relative_to(data_path)
        path = Path("/data", *path.parts[1:])
    except ValueError:
        raise ValueError(
            "Save/load is only allowed from within the `data/{detector_name}` "
            "directory, and the absolute path must be used.")
    return str(path)


HostFilePath = Annotated[
    str,
    AfterValidator(_link_host_file),
]


ContainerFilePath = Annotated[
    str,
    AfterValidator(_host_to_container_path),
]


class BaseInit(BaseModel):
    """
    Pydantic model wrapping all the needed `__init__` arguments.
    Can be subclassed to add detector-specific arguments.
    """
    pass


class BaseTrain(BaseModel):
    """
    Pydantic model wrapping all the needed `train` arguments.
    Can be subclassed to add detector-specific arguments.
    """
    apk_paths: list[HostFilePath]
    labels: list[int]


class BaseTrainResponse(BaseModel):
    """
    Pydantic model wrapping all the returned `train` arguments.
    Can be subclassed to add detector-specific arguments.
    """
    pass


class BaseClassify(BaseModel):
    """
    Pydantic model wrapping all the needed `classify` arguments.
    Can be subclassed to add detector-specific arguments.
    """
    apk_paths: list[HostFilePath]


class BaseClassifyResponse(BaseModel):
    """
    Pydantic model wrapping all the returned `classify` arguments.
    Can be subclassed to add detector-specific arguments.
    """
    labels: list[int]
    scores: list[float]


class BaseSave(BaseModel):
    """
    Pydantic model wrapping all the needed `save` arguments.
    Can be subclassed to add detector-specific arguments.
    """
    path: ContainerFilePath


class BaseLoad(BaseModel):
    """
    Pydantic model wrapping all the needed `load` arguments.
    Can be subclassed to add detector-specific arguments.
    """
    path: ContainerFilePath


class OkResponse(BaseModel):
    """Generic success body."""
    ok: bool


class HealthResponse(BaseModel):
    """Health check body for `/health`."""
    ok: bool
