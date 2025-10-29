import importlib
import os
from fastapi import FastAPI, HTTPException
from core.pydantic_models import *
from core.base_detector import BaseDetector
from core.detector_interface import DetectorInterface


def _import_class(class_path):
    module, cls = class_path.split(":")
    module = importlib.import_module(module)
    return getattr(module, cls)


DETECTOR_MAIN_CLASS = os.getenv("DETECTOR_MAIN_CLASS")
detector_meta: type[BaseDetector] = _import_class(DETECTOR_MAIN_CLASS)
DETECTOR_IMPLEMENTATION_CLASS = os.getenv("DETECTOR_IMPLEMENTATION_CLASS")
detector_cls: type[DetectorInterface] = _import_class(
    DETECTOR_IMPLEMENTATION_CLASS)
detector: DetectorInterface | None = None
app = FastAPI()


@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(ok=True)


@app.post("/init")
def init(
    init_args: detector_meta.init_args,
):
    global detector
    if detector is not None:
        return "Detector already_initialized"
    detector = detector_cls(init_args)
    return "Detector Initialized"


@app.post("/train")
def train(
    train_args: detector_meta.train_args
) -> detector_meta.train_response:
    if detector is None:
        raise HTTPException(400, "Detector not initialized")
    result = detector.train(train_args)
    return result


@app.post("/classify")
def classify(
    classify_args: detector_meta.classify_args
) -> detector_meta.classify_response:
    if detector is None:
        raise HTTPException(400, "Detector not initialized")
    result = detector.classify(classify_args)
    return result


@app.post("/save")
def save(
    save_args: detector_meta.save_args
) -> OkResponse:
    if detector is None:
        raise HTTPException(400, "Detector not initialized")
    detector.save(save_args)
    return OkResponse(ok=True)


@app.post("/load")
def load(
    load_args: detector_meta.load_args
) -> OkResponse:
    if detector is None:
        raise HTTPException(400, "Detector not initialized")
    detector.load(load_args)
    return OkResponse(ok=True)


@app.post("/shutdown")
def shutdown() -> OkResponse:
    os._exit(0)
