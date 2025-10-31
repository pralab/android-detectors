"""
This module contains type annotations that are used to convert the host file
paths, allowing the containerized detectors to safely read/write files from the
host filesystem. To perform the conversion, they must be used for typing the
path arguments in the method. They are then applied by Pydantic, using the
`validate_call` decorator on each method. They will be only applied when
invoked from a containerized detector proxy from the host. Otherwise, they will
keep the paths unaltered.

`HostFilePath` allows reading-only the host files from the container. To do so,
it creates links to the host files inside a folder mounted in read-only mode in
the container's `/shared` folder.

`ContainerFilePath` allows the container to read and write from a folder
`data/{detector_name}` inside this project's root, which is bind inside the
container's `data/` folder.
"""
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
