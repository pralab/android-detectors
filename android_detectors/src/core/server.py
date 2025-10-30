import importlib
import os
from typing import Any
from fastapi import FastAPI, HTTPException, Body
from core.base_detector import BaseDetector
from config import *


def _import_class(class_path):
    module, cls = class_path.split(":")
    module = importlib.import_module(module)
    return getattr(module, cls)


detector_cls: type[BaseDetector] = _import_class(os.getenv(DETECTOR_CLASS))
detector: BaseDetector | None = None
app = FastAPI()


@app.get("/health")
def health():
    return "ok"


@app.post("/shutdown")
def shutdown():
    os._exit(0)


@app.post("/{method_name}")
def init(
    method_name: str,
    payload: dict[str, Any] = Body(),
):
    global detector
    if method_name == "__init__":
        if detector is not None:
            return "Detector already_initialized"
        detector = detector_cls(**payload)
        return "Detector Initialized"
    else:
        if detector is None:
            raise HTTPException(400, "Detector not initialized")
        method = getattr(detector, method_name)
        return method(**payload)
