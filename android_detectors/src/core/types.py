from pydantic import AfterValidator
from typing import Annotated
import os
from config import *


__all__ = ["HostFilePath", "ContainerFilePath"]


def _link_host_file(
    path: str,
) -> str:
    if not os.getenv(DOCKERIZED) == "1":
        return path
    path = Path(path).resolve()
    if not path.is_file():
        raise ValueError(f"File {path} does not exist")
    if os.getenv(RUNNING_IN_CONTAINER) == "1":
        return str(path)
    dest = HOST_SHARED_RO_DATA / path.relative_to(path.anchor)
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        dest.hardlink_to(path)
    except FileExistsError:
        pass
    return str(Path(CONTAINER_SHARED_RO_DATA) / path.relative_to(path.anchor))


def _host_to_container_path(
    path: str,
) -> str:
    if not os.getenv(DOCKERIZED) == "1":
        return path
    path = Path(path).resolve()
    if os.getenv(RUNNING_IN_CONTAINER) == "1":
        return str(path)
    try:
        HOST_SHARED_RW_DATA.mkdir(exist_ok=True)
        path = path.relative_to(HOST_SHARED_RW_DATA)
        path = Path(CONTAINER_SHARED_RW_DATA, *path.parts[1:])
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
