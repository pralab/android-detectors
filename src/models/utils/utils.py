import numpy as np
from matplotlib import pyplot as plt
from sklearn.metrics import roc_curve, auc, confusion_matrix, f1_score, \
    precision_score

__all__ = ["plot_roc", "get_metrics"]


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
