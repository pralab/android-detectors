from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from loaders import drebin_loader, secsvm_loader
from enum import Enum
import numpy as np
import os
import ray
from pathlib import Path
import json
import hashlib


def _get_hash(file_path):
    with open(file_path, mode='rb') as f:
        bytes = f.read()
        sha256_hash = hashlib.sha256(bytes).hexdigest().upper()
    return sha256_hash


class DetectorName(str, Enum):
    drebin = "drebin"
    secsvm = "secsvm"


class DatasetName(str, Enum):
    apg = "apg"
    elsa = "elsa"


data_path = "/homes/data/"
models = {}


def init_models():
    for dataset in DatasetName:
        models[dataset.value] = {}
        for detector in DetectorName:
            if detector is DetectorName.drebin:
                model = drebin_loader.load(data_path, dataset.value)
            elif detector is DetectorName.secsvm:
                model = secsvm_loader.load(data_path, dataset.value)
            else:
                raise ValueError(f"Unknown detector: {detector.value}")
            models[dataset.value][detector.value] = model


def extract_features(
        detector: DetectorName,
        dataset: DatasetName,
        apk_path: str
):
    features = None
    features_dir = Path(data_path) / dataset.value / "drebin" / "features"
    features_file = (features_dir / _get_hash(apk_path)).with_suffix(".json")
    if features_file.exists():
        with open(features_file) as f:
            js = json.load(f)
            return [[f"{k}::{v}" for k in js for v in js[k] if js[k]]]
    try:
        features = models[dataset.value][detector.value].extract_features(
            [apk_path])
    except:
        import traceback
        traceback.print_exc()
    return features


def predict(
        detector: DetectorName,
        dataset: DatasetName,
        features: np.ndarray
) -> tuple[int, float]:
    model = models[dataset.value][detector.value]
    y_pred, score = model.predict(features)
    return y_pred.item(), score.item()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # on start
    ray.init(
        ignore_reinit_error=True
    )
    init_models()
    yield
    # on close
    ray.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/{detector}/{dataset}")
def classify(
        detector: DetectorName,
        dataset: DatasetName,
        apk_path: str
):
    if not os.path.isfile(apk_path):
        raise HTTPException(status_code=404, detail="APK not found")
    features = extract_features(detector, dataset, apk_path)
    if features is None:
        return JSONResponse((None, None), status_code=500)
    return predict(detector, dataset, features)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("serve_detector:app", port=8000, reload=False)
