import json
import os
from src.models import DREBIN
from src.models.utils import *


if __name__ == "__main__":
    classifier = DREBIN(C=0.1)

    base_path = os.path.dirname(__file__)

    clf_path = os.path.join(
        base_path, "../pretrained/drebin_vectorizer.pkl")
    vect_path = os.path.join(
        base_path, "../pretrained/drebin_classifier.pkl")

    if os.path.exists(clf_path) and os.path.exists(vect_path):
        classifier = DREBIN.load(vect_path, clf_path)
    else:
        features_tr = load_features(
            os.path.join(base_path, "data/training_set_features.zip"))
        y_tr = load_labels(
            os.path.join(base_path, "data/training_set_features.zip"),
            os.path.join(base_path, "data/training_set.zip"))
        classifier.fit(features_tr, y_tr)
        classifier.save(vect_path, clf_path)

    results = []
    for i in range(1, 5):
        features_ts = load_features(
            os.path.join(base_path, f"data/test_set_features_round_{i}.zip"))
        y_pred, scores = classifier.predict(features_ts)
        results.append({
            sha256: [int(y), float(s)] for sha256, y, s in zip(
                load_sha256_list(os.path.join(
                    base_path, f"data/test_set_features_round_{i}.zip")),
                y_pred, scores)})

    with open(os.path.join(
            base_path, "submissions/submission_drebin_track_3.json"),
              "w") as f:
        json.dump(results, f)
