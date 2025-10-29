from core.base_detector import BaseDetector
from .pydantic_models import *
from detectors.drebin.pydantic_models import DrebinSaveLoad


class SecSVM(BaseDetector):
    name = "secsvm"
    implementation_module = "implementation"
    implementation_class = "SecSVM"
    init_args = SecSVMInit
    save_args = DrebinSaveLoad
    load_args = DrebinSaveLoad
    image_tag = "secsvm:latest"
