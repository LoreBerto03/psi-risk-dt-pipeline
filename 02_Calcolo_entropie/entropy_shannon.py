import numpy as np


def shannon_entropy(window: np.ndarray, bins: int = 16, value_range=None) -> float:
    """
    Calcola l'entropia di Shannon su una finestra numerica
    usando un istogramma discreto.

    Parameters
    ----------
    window : np.ndarray
        Finestra di valori.
    bins : int
        Numero di bin dell'istogramma.
    value_range : tuple | None
        Range globale (min, max) da usare per avere confronti coerenti.

    Returns
    -------
    float
        Entropia di Shannon in bit.
    """
    window = np.asarray(window, dtype=float)

    if window.size == 0:
        return 0.0

    if np.allclose(window.min(), window.max()):
        return 0.0

    counts, _ = np.histogram(window, bins=bins, range=value_range)

    total = counts.sum()
    if total == 0:
        return 0.0

    probs = counts[counts > 0] / total
    return float(-np.sum(probs * np.log2(probs)))