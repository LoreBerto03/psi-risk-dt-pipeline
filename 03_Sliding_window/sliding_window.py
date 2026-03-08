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
    STEP,
    ENTROPY_BINS,
    ensure_directories,
    FUSEKI_BASE_URL,
    FUSEKI_DATASET,
)
from entropy_shannon import shannon_entropy
from docker_utils import wait_for_http, fetch_fuseki_points


def load_raw_data() -> pd.DataFrame:
    print(f"[INFO] Attendo Fuseki su {FUSEKI_BASE_URL} ...")
    wait_for_http(f"{FUSEKI_BASE_URL}/$/ping", timeout_seconds=60)

    print(f"[INFO] Lettura dati reali da Fuseki dataset '{FUSEKI_DATASET}' ...")
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


def compute_entropy_over_time(
    values: np.ndarray,
    scenario: str,
    window_sizes: list[int],
    step: int,
    bins: int,
) -> pd.DataFrame:
    rows = []

    global_min = float(np.min(values))
    global_max = float(np.max(values))

    if np.isclose(global_min, global_max):
        global_max = global_min + 1e-9

    value_range = (global_min, global_max)

    for window_size in window_sizes:
        previous_h = None

        for start in range(0, len(values) - window_size + 1, step):
            end = start + window_size
            window = values[start:end]

            h = shannon_entropy(window, bins=bins, value_range=value_range)
            delta_h = np.nan if previous_h is None else h - previous_h

            rows.append(
                {
                    "scenario": scenario,
                    "window_size": window_size,
                    "t_start": start,
                    "t_end": end - 1,
                    "entropy_shannon": h,
                    "delta_h": delta_h,
                }
            )

            previous_h = h

    return pd.DataFrame(rows)


def main() -> None:
    ensure_directories()

    output_dir = PROJECT_ROOT / "05_Risultati" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "entropy_final.csv"

    df = load_raw_data()

    all_results = []
    for scenario, group in df.groupby("scenario", sort=True):
        values = group["value"].to_numpy(dtype=float)

        if len(values) < min(WINDOW_SIZES):
            print(
                f"[WARN] Scenario '{scenario}' ignorato: "
                f"{len(values)} punti < finestra minima {min(WINDOW_SIZES)}"
            )
            continue

        scenario_results = compute_entropy_over_time(
            values=values,
            scenario=scenario,
            window_sizes=WINDOW_SIZES,
            step=STEP,
            bins=ENTROPY_BINS,
        )
        all_results.append(scenario_results)

    if not all_results:
        raise RuntimeError(
            "Nessun risultato prodotto. "
            "Controlla i dati in Fuseki o riduci WINDOW_SIZES."
        )

    result_df = pd.concat(all_results, ignore_index=True)
    result_df.to_csv(output_file, index=False)

    print(f"[OK] Risultato finale salvato in: {output_file}")
    print(result_df.head())


if __name__ == "__main__":
    main()