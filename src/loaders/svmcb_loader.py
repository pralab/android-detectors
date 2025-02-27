import os
import models
from models import SVMCustomBounds
from models.utils import *

from zipfile import ZipFile, ZIP_DEFLATED
import json
import pandas as pd
import numpy as np
from datetime import datetime

def load_timestamps(features_path, ds_data_path, i=1):
    """

    Parameters
    ----------
    features_path : str
        Absolute path of the features compressed file.
    ds_data_path : str
        Absolute path of the data file (json or compressed csv) containing
        the labels.
    i : int
        If a json file is provided, specify the index to select.

    Returns
    -------
    np.ndarray
        Array of shape (n_samples,) containing the timestamps.
    """
    if ds_data_path.endswith(".json"):
        with open(ds_data_path, "r") as f:
            timestamp_json = {k: v for k, v in json.load(f)[i].items()}
    else:
        with ZipFile(ds_data_path, "r", ZIP_DEFLATED) as z:
            ds_csv = pd.concat(
                [pd.read_csv(z.open(f))[["sha256", "timestamp"]]
                 for f in z.namelist()], ignore_index=True)
            timestamp_json = {k: v for k, v in zip(ds_csv.sha256.values,
                                                   ds_csv.timestamp.values)}

    with ZipFile(features_path, "r", ZIP_DEFLATED) as z:
        # timestamps = [timestamp_json[f.split(".json")[0].lower()]
        #           for f in z.namelist()]
        timestamps = [datetime.strptime(
            timestamp_json[f.split(".json")[0].lower()],
            "%Y-%m-%d %H:%M:%S")
                  for f in z.namelist()]

    return np.array(timestamps)

def load(clf_name='svmcb', b=0.8, n_unst=100, max_it=1000):
    """
    NB: in this example, the pre-extracted features are used. Alternatively,
    the APK file paths can be passed to the classifier.
    To fit the model, you can use `classifier.extract_features` to get the
    features and then pass them to `classifier.fit`.
    To classify the APK files, you can directly pass the list containing the
    file paths to `classifier.classify`.
    """
    classifier = SVMCustomBounds(C=0.1, lb=-b, ub=b, n_unstable_features=n_unst,
                                 max_it=max_it)

    model_base_path = os.path.join(os.path.dirname(models.__file__), "../..")

    clf_path = os.path.join(
        model_base_path, f"pretrained/{clf_name}_classifier.pkl")
    vect_path = os.path.join(
        model_base_path, f"pretrained/{clf_name}_vectorizer.pkl")

    if os.path.exists(clf_path) and os.path.exists(vect_path):
        classifier = SVMCustomBounds.load(vect_path, clf_path)
    else:
        features_tr = load_features(
            os.path.join("data/training_set_features.zip"))
        y_tr = load_labels("data/training_set_features.zip",
                           "data/training_set.zip")
        t_tr = load_timestamps("data/training_set_features.zip",
                           "data/training_set.zip")
        classifier.fit(features_tr, y_tr, t_tr)
        classifier.save(vect_path, clf_path)

    return classifier
