import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
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
    ENTROPY_BINS,
    iter_experiment_configurations,
    ensure_directories,
    FUSEKI_BASE_URL,
    FUSEKI_DATASET,
)
from entropy_shannon import shannon_entropy
from entropy_sample import sample_entropy
from entropy_permutation import permutation_entropy
from docker_utils import wait_for_http, fetch_fuseki_points

BASELINE_SCENARIO = "stable"
THRESHOLD_STD_FACTOR = 3.0

SAMPLE_ENTROPY_M = 2
SAMPLE_ENTROPY_R_RATIO = 0.2
PERMUTATION_ORDER = 3
PERMUTATION_DELAY = 1

MAX_WORKERS = int(os.getenv("SLIDING_MAX_WORKERS", str(os.cpu_count() or 1)))


def compute_delta(current: float, previous: float | None) -> float:
    if previous is None:
        return np.nan
    if not np.isfinite(current) or not np.isfinite(previous):
        return np.nan
    return float(current - previous)


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


def compute_entropy_for_configuration(task: dict) -> pd.DataFrame:
    configuration = task["configuration"]
    scenario = task["scenario"]
    values = task["values"]
    times = task["times"]
    window_size = task["window_size"]
    stride = task["stride"]
    bins = task["bins"]
    value_range = task["value_range"]
    residual_threshold = task["residual_threshold"]

    rows = []

    previous_shannon = None
    previous_sample = None
    previous_permutation = None

    for start in range(0, len(values) - window_size + 1, stride):
        end = start + window_size

        window = values[start:end]
        window_times = times[start:end]

        h_shannon = shannon_entropy(
            window,
            bins=bins,
            value_range=value_range,
        )

        h_sample = sample_entropy(
            window,
            m=SAMPLE_ENTROPY_M,
            r_ratio=SAMPLE_ENTROPY_R_RATIO,
        )

        h_permutation = permutation_entropy(
            window,
            order=PERMUTATION_ORDER,
            delay=PERMUTATION_DELAY,
            normalize=True,
        )

        delta_h_shannon = compute_delta(h_shannon, previous_shannon)
        delta_h_sample = compute_delta(h_sample, previous_sample)
        delta_h_permutation = compute_delta(h_permutation, previous_permutation)

        abs_window = np.abs(window)

        rows.append(
            {
                "configuration": configuration,
                "scenario": scenario,
                "window_size": int(window_size),
                "stride": int(stride),
                "t_start": float(window_times[0]),
                "t_center": float(window_times[len(window_times) // 2]),
                "t_end": float(window_times[-1]),

                "entropy_shannon": float(h_shannon),
                "entropy_sample": float(h_sample),
                "entropy_permutation": float(h_permutation),

                "delta_h_shannon": (
                    np.nan if np.isnan(delta_h_shannon) else float(delta_h_shannon)
                ),
                "delta_h_shannon_abs": (
                    np.nan if np.isnan(delta_h_shannon) else float(abs(delta_h_shannon))
                ),

                "delta_h_sample": (
                    np.nan if np.isnan(delta_h_sample) else float(delta_h_sample)
                ),
                "delta_h_sample_abs": (
                    np.nan if np.isnan(delta_h_sample) else float(abs(delta_h_sample))
                ),

                "delta_h_permutation": (
                    np.nan
                    if np.isnan(delta_h_permutation)
                    else float(delta_h_permutation)
                ),
                "delta_h_permutation_abs": (
                    np.nan
                    if np.isnan(delta_h_permutation)
                    else float(abs(delta_h_permutation))
                ),

                # compatibilità col plot baseline_vs_entropy già esistente
                "delta_h": (
                    np.nan if np.isnan(delta_h_shannon) else float(delta_h_shannon)
                ),
                "delta_h_abs": (
                    np.nan if np.isnan(delta_h_shannon) else float(abs(delta_h_shannon))
                ),

                "abs_dt_mean": float(abs_window.mean()),
                "abs_dt_max": float(abs_window.max()),
                "over_threshold_ratio": float(
                    (abs_window > residual_threshold).mean()
                ),
                "residual_threshold": float(residual_threshold),
            }
        )

        previous_shannon = h_shannon
        previous_sample = h_sample
        previous_permutation = h_permutation

    return pd.DataFrame(rows)


def build_tasks(
    df: pd.DataFrame,
    configurations,
    bins: int,
    value_range: tuple[float, float],
    residual_threshold: float,
) -> list[dict]:
    tasks = []
    min_window_size = min(int(config["window_size"]) for config in configurations)

    for scenario, group in df.groupby("scenario", sort=True):
        values = group["value"].to_numpy(dtype=float)
        times = group["t"].to_numpy(dtype=float)

        if len(values) < min_window_size:
            print(
                f"[WARN] Scenario '{scenario}' ignorato: "
                f"{len(values)} punti < finestra minima {min_window_size}"
            )
            continue

        for config in configurations:
            tasks.append(
                {
                    "configuration": str(config["id"]),
                    "scenario": scenario,
                    "values": values,
                    "times": times,
                    "window_size": int(config["window_size"]),
                    "stride": int(config["stride"]),
                    "bins": int(bins),
                    "value_range": value_range,
                    "residual_threshold": float(residual_threshold),
                }
            )

    return tasks


def run_tasks_parallel(tasks: list[dict]) -> list[pd.DataFrame]:
    if not tasks:
        return []

    workers = max(1, min(MAX_WORKERS, len(tasks)))
    print(f"[INFO] Avvio calcolo parallelo con {workers} worker(s) su {len(tasks)} task")

    results = []

    if workers == 1:
        for idx, task in enumerate(tasks, start=1):
            print(
                f"[INFO] Task {idx}/{len(tasks)} -> "
                f"config={task['configuration']}, scenario={task['scenario']}, "
                f"W={task['window_size']}, stride={task['stride']}"
            )
            results.append(compute_entropy_for_configuration(task))
        return results

    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_task = {
            executor.submit(compute_entropy_for_configuration, task): task
            for task in tasks
        }

        completed = 0
        total = len(tasks)

        for future in as_completed(future_to_task):
            task = future_to_task[future]
            completed += 1

            print(
                f"[INFO] Completato task {completed}/{total} -> "
                f"config={task['configuration']}, scenario={task['scenario']}, "
                f"W={task['window_size']}, stride={task['stride']}"
            )

            results.append(future.result())

    return results


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

    tasks = build_tasks(
        df=df,
        configurations=iter_experiment_configurations(include_reference=True),
        bins=ENTROPY_BINS,
        value_range=global_value_range,
        residual_threshold=residual_threshold,
    )

    if not tasks:
        raise RuntimeError(
            "Nessun task creato. Controlla i dati in Fuseki o la griglia sperimentale."
        )

    all_results = run_tasks_parallel(tasks)

    if not all_results:
        raise RuntimeError("Nessun risultato prodotto durante il calcolo.")

    result_df = pd.concat(all_results, ignore_index=True)
    result_df = result_df.sort_values(
        ["configuration", "scenario", "t_start"]
    ).reset_index(drop=True)

    result_df.to_csv(entropy_output_file, index=False)

    print(f"[OK] Risultato finale salvato in: {entropy_output_file}")
    print(result_df.head())


if __name__ == "__main__":
    main()
