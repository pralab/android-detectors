from core.base_detector import BaseDetector
from .pydantic_models import *


class DREBIN(BaseDetector):
    name = "drebin"
    implementation_module = "implementation"
    implementation_class = "DREBIN"
    init_args = DrebinInit
    train_args = DrebinTrain
    classify_args = DrebinClassify
    save_args = DrebinSaveLoad
    load_args = DrebinSaveLoad
    image_tag = "drebin:latest"
