from zipfile import ZipFile, ZIP_DEFLATED
import json
import pandas as pd
import numpy as np


__all__ = ["load_features", "load_labels", "load_sha256_list"]


def load_features(features_path):
    """

    Parameters
    ----------
    features_path :
        Absolute path of the features compressed file.

    Returns
    -------
    generator of list of strings
        Iteratively returns the textual feature vector of each sample.
    """
    with ZipFile(features_path, "r", ZIP_DEFLATED) as z:
        for filename in z.namelist():
            with z.open(filename) as fp:
                js = json.load(fp)
                yield [f"{k}::{v}" for k in js for v in js[k] if js[k]]


def load_labels(features_path, ds_data_path, i=1):
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
        Array of shape (n_samples,) containing the class labels.
    """
    if ds_data_path.endswith(".json"):
        with open(ds_data_path, "r") as f:
            labels_json = {k: v for k, v in json.load(f)[i].items()}
    else:
        with ZipFile(ds_data_path, "r", ZIP_DEFLATED) as z:
            ds_csv = pd.concat(
                [pd.read_csv(z.open(f))[["sha256", "label"]]
                 for f in z.namelist()], ignore_index=True)
            labels_json = {k: v for k, v in zip(ds_csv.sha256.values,
                                                ds_csv.label.values)}

    with ZipFile(features_path, "r", ZIP_DEFLATED) as z:
        labels = [labels_json[f.split(".json")[0].lower()]
                  for f in z.namelist()]
    return np.array(labels)


def load_sha256_list(features_path):
    """

    Parameters
    ----------
    features_path :
        Absolute path of the features compressed file.

    Returns
    -------
    list of strings
        List containing the sha256 hash of the APK files.
    """
    with ZipFile(features_path, "r", ZIP_DEFLATED) as z:
        return [filename.split(".")[0] for filename in z.namelist()]
