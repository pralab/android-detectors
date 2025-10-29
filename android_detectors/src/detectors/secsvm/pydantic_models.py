from core.pydantic_models import *


class SecSVMInit(BaseInit):
    """
    Parameters
    ----------
    C : float, optional
        Penalty hyper-parameter C of the error term. Default 1.0.
    kernel : None or CKernel subclass, optional
        Instance of a CKernel subclass to be used for computing
        similarity between patterns. If None (default), a linear
        SVM is trained in the primal; otherwise an SVM is trained in the dual,
        using the precomputed kernel values.
    class_weight : {dict, 'balanced', None}, optional
        Set the parameter C of class i to `class_weight[i] * C`.
        If not given (default), all classes are supposed to have
        weight one. The 'balanced' mode uses the values of labels to
        automatically adjust weights inversely proportional to
        class frequencies as `n_samples / (n_classes * np.bincount(y))`.
    ub : scalar or None, optional
        Upper bound of the weights. If None (default), no bound is applied.
    idx_ub : CArray or None, optional
        If CArray, the upper bound is only applied to the weights indicized
        by `idx_ub`. If None (default), the bound is applied to all weights.
    lb : scalar or None, optional
        Lower bound of the weights. If None (default), no bound is applied.
    idx_lb : CArray or None, optional
        If CArray, the lower bound is only applied to the weights indicized
        by `idx_ub`. If None (default), the bound is applied to all weights.
    eta : scalar, optional
        Step of the gradient descent. Default 0.5.
    max_it : int, optional
        Maximum number of iterations of the gradient descent. Default 1e4.
    eps : scalar, optional
        Tolerance of the stop criterion of the gradient descent. Default 1e-4.
    """
    C: float = 0.1
    kernel: None | str = None
    class_weight: dict | str | None = None
    ub: float = float("inf")
    idx_ub: list[int] | None = None
    lb: float = float("-inf")
    idx_lb: list[int] | None = None
    eta: float = 0.5
    max_it: int = 1e4
    eps: float = 1e-4
