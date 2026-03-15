import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENTROPY_MODULE_DIR = PROJECT_ROOT / "02_Calcolo_entropie"
CONFIG_DIR = PROJECT_ROOT / "Config"

for p in [PROJECT_ROOT, ENTROPY_MODULE_DIR, CONFIG_DIR]:
    if str(p) not in sys.path:
        sys.path.append(str(p))

from config import (
    WINDOW_SIZES,
    STRIDES,
    ENTROPY_BINS,
    ensure_directories,
    FUSEKI_BASE_URL,
    FUSEKI_DATASET,
)
from entropy_shannon import shannon_entropy
from docker_utils import wait_for_http, fetch_fuseki_points

BASELINE_SCENARIO = "stable"
THRESHOLD_STD_FACTOR = 3.0


def load_raw_data() -> pd.DataFrame:
    print(f"[INFO] Attendo Fuseki su {FUSEKI_BASE_URL} ...")
    wait_for_http(f"{FUSEKI_BASE_URL}/$/ping", timeout_seconds=60)

    print(f"[INFO] Lettura dati da Fuseki dataset '{FUSEKI_DATASET}' ...")
    df = fetch_fuseki_points(FUSEKI_BASE_URL, FUSEKI_DATASET)

    required_columns = {"scenario", "t", "value"}
    missing = required_columns - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Dati Fuseki non validi. Mancano le colonne: {sorted(missing)}"
        )

    df = df.sort_values(["scenario", "t"]).reset_index(drop=True)

    print(f"[INFO] Righe caricate da Fuseki: {len(df)}")
    print(df.head())
    return df


def compute_baseline_threshold(
    df: pd.DataFrame,
    baseline_scenario: str = BASELINE_SCENARIO,
    k: float = THRESHOLD_STD_FACTOR,
) -> float:
    baseline_df = df[
        df["scenario"].astype(str).str.lower() == baseline_scenario.lower()
    ].copy()

    if baseline_df.empty:
        raise RuntimeError(
            f"Scenario baseline '{baseline_scenario}' non trovato nei dati."
        )

    abs_values = np.abs(baseline_df["value"].to_numpy(dtype=float))
    threshold = float(abs_values.mean() + k * abs_values.std(ddof=0))

    print(f"[INFO] Soglia baseline calcolata da '{baseline_scenario}': {threshold:.6f}")
    return threshold


def compute_entropy_over_time(
    values: np.ndarray,
    times: np.ndarray,
    scenario: str,
    window_sizes: list[int],
    strides: list[int],
    bins: int,
    value_range: tuple[float, float],
    residual_threshold: float,
) -> pd.DataFrame:
    rows = []

    for window_size in window_sizes:
        for stride in strides:
            previous_h = None

            for start in range(0, len(values) - window_size + 1, stride):
                end = start + window_size

                window = values[start:end]
                window_times = times[start:end]

                h = shannon_entropy(window, bins=bins, value_range=value_range)
                delta_h = np.nan if previous_h is None else h - previous_h
                abs_window = np.abs(window)

                rows.append(
                    {
                        "scenario": scenario,
                        "window_size": int(window_size),
                        "stride": int(stride),
                        "t_start": float(window_times[0]),
                        "t_center": float(window_times[len(window_times) // 2]),
                        "t_end": float(window_times[-1]),
                        "entropy_shannon": float(h),
                        "delta_h": np.nan if previous_h is None else float(delta_h),
                        "delta_h_abs": np.nan if previous_h is None else float(abs(delta_h)),
                        "abs_dt_mean": float(abs_window.mean()),
                        "abs_dt_max": float(abs_window.max()),
                        "over_threshold_ratio": float((abs_window > residual_threshold).mean()),
                        "residual_threshold": float(residual_threshold),
                    }
                )

                previous_h = h

    return pd.DataFrame(rows)


def main() -> None:
    ensure_directories()

    output_dir = PROJECT_ROOT / "05_Risultati" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_output_file = output_dir / "raw_points.csv"
    entropy_output_file = output_dir / "entropy_final.csv"

    df = load_raw_data()

    df.to_csv(raw_output_file, index=False)
    print(f"[OK] Dati grezzi salvati in: {raw_output_file}")

    global_min = float(df["value"].min())
    global_max = float(df["value"].max())
    if np.isclose(global_min, global_max):
        global_max = global_min + 1e-9

    global_value_range = (global_min, global_max)
    residual_threshold = compute_baseline_threshold(df)

    all_results = []
    for scenario, group in df.groupby("scenario", sort=True):
        values = group["value"].to_numpy(dtype=float)
        times = group["t"].to_numpy(dtype=float)

        if len(values) < min(WINDOW_SIZES):
            print(
                f"[WARN] Scenario '{scenario}' ignorato: "
                f"{len(values)} punti < finestra minima {min(WINDOW_SIZES)}"
            )
            continue

        scenario_results = compute_entropy_over_time(
            values=values,
            times=times,
            scenario=scenario,
            window_sizes=WINDOW_SIZES,
            strides=STRIDES,
            bins=ENTROPY_BINS,
            value_range=global_value_range,
            residual_threshold=residual_threshold,
        )
        all_results.append(scenario_results)

    if not all_results:
        raise RuntimeError(
            "Nessun risultato prodotto. Controlla i dati in Fuseki o riduci WINDOW_SIZES."
        )

    result_df = pd.concat(all_results, ignore_index=True)
    result_df.to_csv(entropy_output_file, index=False)

    print(f"[OK] Risultato finale salvato in: {entropy_output_file}")
    print(result_df.head())


if __name__ == "__main__":
    main()