import numpy as np


def sample_entropy(
    window: np.ndarray,
    m: int = 2,
    r_ratio: float = 0.2,
    continuity_correction: float = 1.0,
) -> float:
    """
    Calcola la Sample Entropy su una finestra numerica.

    Parameters
    ----------
    window : np.ndarray
        Finestra di valori.
    m : int
        Dimensione dei pattern da confrontare.
    r_ratio : float
        Tolleranza relativa rispetto alla deviazione standard della finestra.
    continuity_correction : float
        Correzione additiva usata solo quando A = 0 per evitare di restituire
        uno zero spurio dovuto al campione finito.

    Returns
    -------
    float
        Sample Entropy.
    """
    window = np.asarray(window, dtype=float)
    window = window[np.isfinite(window)]

    if m < 1:
        raise ValueError("m deve essere >= 1")
    if r_ratio <= 0:
        raise ValueError("r_ratio deve essere > 0")
    if continuity_correction < 0:
        raise ValueError("continuity_correction deve essere >= 0")

    if window.size <= m + 1:
        return float("nan")

    std = np.std(window)
    if np.isclose(std, 0.0):
        return 0.0

    r = max(r_ratio * std, np.finfo(float).eps)

    def _embed(length: int) -> np.ndarray:
        n_vectors = window.size - length + 1
        if n_vectors <= 1:
            return np.empty((0, length), dtype=float)
        return np.lib.stride_tricks.sliding_window_view(window, length)

    def _count_matches(embedded: np.ndarray) -> int:
        n = embedded.shape[0]
        if n < 2:
            return 0

        diff = np.abs(embedded[:, None, :] - embedded[None, :, :])
        chebyshev_dist = np.max(diff, axis=2)

        upper_idx = np.triu_indices(n, k=1)
        return int(np.sum(chebyshev_dist[upper_idx] <= r))

    emb_m = _embed(m)
    emb_m1 = _embed(m + 1)

    B = _count_matches(emb_m)
    A = _count_matches(emb_m1)

    if B == 0:
        return float("nan")

    if A == 0:
        if continuity_correction == 0:
            return float("inf")
        return float(-np.log(continuity_correction / (B + continuity_correction)))

    return float(-np.log(A / B))
