from zipfile import ZipFile, ZIP_DEFLATED
import json
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn.metrics import roc_curve, auc, confusion_matrix, f1_score, \
    precision_score

__all__ = ["load_features", "load_labels", "load_sha256_list", "plot_roc",
           "get_metrics"]


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


def plot_roc(y_true, scores, img_path="", title="Roc"):
    fpr, tpr, th = roc_curve(y_true, scores)
    roc_auc = auc(fpr, tpr)

    plt.semilogx(fpr, tpr, color="darkorange", lw=2,
                 label=f"AUC = {roc_auc:0.2f}")
    plt.axvline(fpr[np.argmin(np.abs(th))], color="k", linestyle="--")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title(title)
    plt.legend(loc="lower right")
    if img_path > "":
        plt.savefig(img_path)
    plt.show()
    plt.clf()


def get_metrics(y_true, y_pred):

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    print(f"F1 Score: {f1_score(y_true, y_pred):.4f}")
    print(f"Precision: {precision_score(y_true, y_pred):.4f}")
    print(f"TPR (aka Recall): {tp / (tp + fn):.4f}")
    print(f"FPR: {fp / (fp + tn):.4f}")
