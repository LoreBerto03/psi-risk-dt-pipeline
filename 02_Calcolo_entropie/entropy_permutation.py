import math
import numpy as np


def permutation_entropy(
    window: np.ndarray,
    order: int = 3,
    delay: int = 1,
    normalize: bool = True
) -> float:
    """
    Calcola la Permutation Entropy su una finestra numerica.

    Parameters
    ----------
    window : np.ndarray
        Finestra di valori.
    order : int
        Dimensione del pattern ordinale.
    delay : int
        Passo tra i campioni del pattern.
    normalize : bool
        Se True normalizza il valore tra 0 e 1.

    Returns
    -------
    float
        Permutation Entropy.
    """
    window = np.asarray(window, dtype=float)
    window = window[np.isfinite(window)]

    if order < 2:
        raise ValueError("order deve essere >= 2")
    if delay < 1:
        raise ValueError("delay deve essere >= 1")

    required_size = 1 + (order - 1) * delay
    if window.size < required_size:
        return float("nan")

    if np.allclose(window, window[0]):
        return 0.0

    patterns = []

    for i in range(window.size - required_size + 1):
        subseq = window[i:i + required_size:delay]
        if subseq.size != order:
            continue
        pattern = tuple(np.argsort(subseq, kind="mergesort"))
        patterns.append(pattern)

    if len(patterns) == 0:
        return float("nan")

    _, counts = np.unique(patterns, axis=0, return_counts=True)
    probs = counts / counts.sum()

    entropy = -np.sum(probs * np.log2(probs))

    if normalize:
        entropy /= np.log2(math.factorial(order))

    return float(entropy)
