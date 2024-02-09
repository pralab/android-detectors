# Android Malware Detectors
End-to-end implementation of ML-based Android malware detectors.

## Available Detectors
- **DREBIN** from Arp, Daniel, et al. "Drebin: Effective and explainable detection of
      android malware in your pocket." NDSS 2014. [[paper]](https://www.ndss-symposium.org/wp-content/uploads/2017/09/11_3_1.pdf)
- **SecSVM** from Demontis et al. "Yes, machine learning can be more secure! a case study
     on android malware detection." IEEE TDSC 2017. [[paper]](https://arxiv.org/abs/1704.08996)
- A **BaseDREBIN** class is also provided, allowing to easily and efficiently train any classifier on the DREBIN feature set by extending a few methods.

## ELSA Cybersecurity Benchmarks
The implemented detectors serve as baselines for the [benchmarks](https://benchmarks.elsa-ai.eu/?ch=6) hosted in the Cybersecurity Use Case of the ELSA EU project.

This repository should be used as a starting point to build a model and submit the results on a competition track. A step-by-step guide can be found below. Please also remember to read all the rules provided [here](https://benchmarks.elsa-ai.eu/?ch=6&com=tasks).

### Implementation instructions
- The model class must necessarily expose a small set of methods. All the details can be found in the [BaseModel](https://github.com/pralab/android-detectors/src/base/base_model.py) class. We suggest to extend this class when implementing your own detector.
- To ensure reproducibility and allow validating the results, make sure to set all random seeds, add all the requirements, and if necessary a Dockerfile from where to run the evaluation scripts.
- Provide one or more scripts for model training and evaluation (including the submission file creation).

### Submission
- The submission of the results for the open tracks can be performed on the [ELSA benchmarks website](https://benchmarks.elsa-ai.eu/?ch=6&com=mymethods). For all the evaluation tracks, the submission must be uploaded in a JSON file, containing a list with a dictionary for each evaluation round (the first dictionary corresponds to the first round, and so on). The keys of each dictionary are the SHA256 hashes of the test set samples for the respective round. An array containing the predicted class label (either 0 or 1) and the positive class score must be associated with each SHA256 hash.
```
[
  {
    sha256: [label, score],
    …
  },
  …
]
```

### Run the example code
Download all the datasets and pre-computed features from the [ELSA benchmarks website](https://benchmarks.elsa-ai.eu/?ch=6&com=downloads) inside the `elsa-benchmarks/data` directory.

If you want to use Docker, you can use the following commands:
```bash
docker build -t android .
docker run -it --name android android python /android-detectors/elsa-benchmarks/drebin_track_3.py
```
The submission file and the pretrained model files can be gathered from the container:
```bash
docker cp android:/android-detectors/elsa-benchmarks/submissions/submission_drebin_track_3.json elsa-benchmarks/submissions/
docker cp android:/android-detectors/pretrained/drebin_classifier.pkl pretrained/
docker cp android:/android-detectors/pretrained/drebin_vectorizer.pkl pretrained/
```

If you don't want to use Docker, it is recommended to create a new environment, for instance if you use conda you can run (it might be required to append `src` directory to the python path before launching the script):
```bash
conda create -n android python=3.9
conda activate android
pip install -r ./requirements.txt
python3 elsa-benchmarks/drebin_track_3.py
```

Pre-trained models can also be downloaded from Drive:
- [DREBIN](https://drive.google.com/drive/folders/118Eb_KoW6vE38aqDY0MmVfHUtLOwO8Vk?usp=sharing)
- [SecSVM](https://drive.google.com/drive/folders/1pSO0UWvBJsrkIgshYkHwR3OqR_slZGBH?usp=sharing)

The downloaded files must be placed in the `pretrained` folder.