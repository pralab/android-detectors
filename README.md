# Android Malware Detectors
End-to-end implementation of ML-based Android malware detectors.
Each detector can be used directly in the client environment or deployed inside
an object-level Docker container, in a transparent manner. In this way, you can use
different detectors from the same program, without needing to install any dependencies.


### Detector common interface
Each detector provides five main methods (with customizable parameters):
- **__init__**: initialize the detector;
- **train**: train the detector on the given APK files;
- **classify**: classify the given APK files and return the predicted labels and scores;
- **save**: save the trained model;
- **load**: load a pretrained model.

---

## How to use it - with dockerized detectors
1. Install the main project requirements with:
```shell
pip install -r src/requirements.txt
```
2. Import the detector class directly from its package, and instantiate it:
```python
from detectors.drebin import DREBIN


drebin_detector = DREBIN(C=0.1)
...
```
That's all! 
The detectors will be able to **read only** the passed host files, while other
read/write operations are only allowed from the `data/{detector_name}` folders
in this project's root.
Alternatively, you can directly import the dockerized detector classes:
```python
from detectors.drebin.drebin_dockerized import DREBIN


...
```

### How it works
During the object instantiation, an ad-hoc Docker container is launched, and the
detector instance is executed inside it. On the container side, a FastAPI application
exposes the detector's interface through APIs. On the client side, a proxy performs
HTTP requests and returns the responses. Note that the image building will happen
once for each detector class, whereas each of its instances will be hosted in a
separate container.

## How to use it - directly on your environment
1. Install both the main project's and the detector's specific requirements.
For examples, to directly use Drebin:
```shell
pip install src/requirements.txt
pip install src/detectors/drebin/requirements.txt
```
Note that you must ensure the compatibility between the required Python versions,
and that a detector may also need other kind of requirements or constraints
(e.g., system-level packages), beyond Python libraries.
2. Import the detector class from its concrete implementation, and instantiate it:
```python
from detectors.drebin.drebin import DREBIN


...
```

---

## Implemented Detectors
- **DREBIN** from Arp, Daniel, et al. "Drebin: Effective and explainable detection of
      android malware in your pocket." NDSS 2014. [[paper]](https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf)
- **SecSVM** from Demontis et al. "Yes, machine learning can be more secure! a case study
     on android malware detection." IEEE TDSC 2017. [[paper]](https://arxiv.org/abs/1704.08996)
- A **BaseDREBIN** class is also provided, allowing to easily and efficiently 
train any classifier on the DREBIN feature set by extending a few methods.

### Pre-trained models
Pre-trained models (on the [ELSA dataset](https://benchmarks.elsa-ai.eu/?ch=6&com=downloads)) can also be downloaded from Drive:
- [DREBIN](https://drive.google.com/drive/folders/1EkOpO88p2FOW1NL5H_AbB4EKgfHeynIA?usp=sharing)
- [SecSVM](https://drive.google.com/drive/folders/11AY4ZQH0pExjEhCvFo3J6FpojnR2zWXE?usp=sharing)

The downloaded files must be placed in the `data/{drebin|sec_svm}/pretrained` folder.

---

## How to add a model
If you want to extend the library by adding new detectors, you must follow these steps:
1. Create a new package in the `src/detectors` folder.
2. Inside it, implement your detector by extending the `core.BaseDetector` abstract class.
3. Write the five required methods (`__init__`, `train`, `classify`, `save`, `load`), 
strictly following their interfaces.
4. If you need additional parameters, you can do so, but their types must
be JSON-compatible. The allowed types are: `int`, `float`, `string`, `bool`, `list`,
`dict`, `tuple`, `set`, and `None`.
5. Always use type hints. This is needed for the container's I/O operations
(see the next point) and to ensure consistency.
6. If you need to **read only** host data from the container, use the `HostFilePath`
type hint (from `core.types`) in the method signature, and pass the absolute host
path as a string.
7. If you also need to write data from the container to the host, use the `ContainerFilePath`
type hint (from `core.types`) in the method signature, and pass the absolute host
path as a string. This will allow the container to read and write files from the
`data/{detector_name}` folders in this project's root.
8. If you want to enable the detector dockerization, launch the following script:
```shell
python generate_stub.py [detector module path] --class [detector class name]

# example
python generate_stub.py src/detectors/drebin/drebin.py --class DREBIN
```
This script will automatically generate a stub class in the `{detector_name}_dockerized.py`
module that, when instantiated, will run the detector inside a Docker container.
You can import directly this class in the detector's package `__init__.py` file, e.g.:
```python
from .drebin_dockerized import DREBIN
```
9. Finally, create your Dockerfile inside the detector's package, and customize your
environment as you prefer. It's only required to:
   - make available a working Python>=3.8 enviroment with `pip`;
   - use `/app` as the working directory;
   - copy the entire project folder and install the main project requirements 
during the image building. You can start from this template
(but take a look to the one inside `src/detectors/drebin`):
```dockerfile
# This is customizable...
FROM ...

# The next steps must be always followed----------------------------------
WORKDIR /app
COPY ./requirements.txt /app
RUN pip install -r ./requirements.txt
# -----------------------------------------------------------------------------

# Put here all your required steps... but remember to copy at some point the 
#  project folder inside the app working directory:
# COPY . /app
```
