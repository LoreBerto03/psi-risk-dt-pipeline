import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "Config"

for p in [PROJECT_ROOT, CONFIG_DIR]:
    if str(p) not in sys.path:
        sys.path.append(str(p))

from config import (
    ENTROPY_RESULT_FILE,
    FIGURES_DIR,
    DRIFT_START,
    DRIFT_END,
    SHOCK_CENTER,
    SHOCK_WIDTH,
    ENTROPY_METRICS,
    EXPERIMENT_CONFIGS,
    ensure_directories,
)

THRESHOLD_STD_FACTOR = float(os.getenv("SENSITIVITY_STD_FACTOR", "3.0"))
OUTPUT_FILE = FIGURES_DIR / "run_results_summary.txt"
SCENARIO_ORDER = {"stable": 0, "drift_gradual": 1, "shock": 2}
METRIC_ORDER = {metric: idx for idx, metric in enumerate(ENTROPY_METRICS)}


def find_input_file() -> Path:
    candidates = [
        ENTROPY_RESULT_FILE,
        PROJECT_ROOT / "05_Risultati" / "tables" / "entropy_final.csv",
        PROJECT_ROOT / "05_Risultati" / "tables" / "entropy_over_time.csv",
    ]

    for path in candidates:
        if path.exists():
            print(f"[INFO] File risultati trovato: {path}")
            return path

    searched = "\n".join(str(p) for p in candidates)
    raise FileNotFoundError(
        "Nessun file risultati trovato.\n"
        f"Ho cercato in:\n{searched}\n"
        "Esegui prima 03_Sliding_window/sliding_window.py"
    )


def metric_delta_column(metric: str) -> str:
    mapping = {
        "shannon": "delta_h_shannon_abs",
        "sample": "delta_h_sample_abs",
        "permutation": "delta_h_permutation_abs",
    }
    return mapping[metric]


def metric_pretty_name(metric: str) -> str:
    mapping = {
        "shannon": "Shannon",
        "sample": "Sample",
        "permutation": "Permutation",
    }
    return mapping[metric]


def scenario_pretty_name(scenario: str) -> str:
    mapping = {
        "stable": "Stable",
        "drift_gradual": "Drift",
        "shock": "Shock",
    }
    return mapping.get(str(scenario), str(scenario))


def event_start_for_scenario(scenario: str) -> float | None:
    scenario = str(scenario).strip().lower()

    if scenario == "drift_gradual":
        return float(DRIFT_START)

    if scenario == "shock":
        return float(SHOCK_CENTER - (2 * SHOCK_WIDTH))

    return None


def compute_tau_from_stable(stable_df: pd.DataFrame, delta_col: str) -> float:
    values = stable_df[delta_col].fillna(0.0).to_numpy(dtype=float)
    return float(values.mean() + THRESHOLD_STD_FACTOR * values.std(ddof=0))


def format_time(value: float) -> str:
    if not np.isfinite(value):
        return "N/A"

    rounded = round(float(value))
    if np.isclose(value, rounded):
        return str(int(rounded))

    return f"{float(value):.2f}"


def build_summary(df: pd.DataFrame, time_column: str) -> pd.DataFrame:
    rows = []
    config_order = {config["id"]: idx for idx, config in enumerate(EXPERIMENT_CONFIGS)}

    configs = (
        df[["window_size", "stride", "configuration"]]
        .drop_duplicates()
        .sort_values(["window_size", "stride"])
        .itertuples(index=False)
    )

    for config in configs:
        config_id = str(config.configuration)
        w = int(config.window_size)
        s = int(config.stride)

        config_df = df[
            (df["window_size"] == w) &
            (df["stride"] == s)
        ].copy()

        stable_df = (
            config_df[config_df["scenario"] == "stable"]
            .copy()
            .sort_values(time_column)
        )

        if stable_df.empty:
            continue

        for metric in ENTROPY_METRICS:
            delta_col = metric_delta_column(metric)
            tau = compute_tau_from_stable(stable_df, delta_col)

            for scenario in sorted(
                config_df["scenario"].dropna().unique().tolist(),
                key=lambda value: SCENARIO_ORDER.get(str(value), 99),
            ):
                scenario_df = (
                    config_df[config_df["scenario"] == scenario]
                    .copy()
                    .sort_values(time_column)
                )

                signal = scenario_df[delta_col].fillna(0.0).to_numpy(dtype=float)
                times = scenario_df[time_column].to_numpy(dtype=float)

                if signal.size == 0:
                    continue

                peak_intensity = float(np.max(signal))
                event_start = event_start_for_scenario(scenario)

                if event_start is None:
                    detection_time = np.nan
                    delay = np.nan
                    false_positives = int(np.sum(signal > tau))
                else:
                    pre_mask = times < event_start
                    post_mask = times >= event_start

                    false_positives = int(np.sum(signal[pre_mask] > tau)) if np.any(pre_mask) else 0

                    post_times = times[post_mask]
                    post_signal = signal[post_mask]
                    detections = post_times[post_signal > tau]

                    if detections.size > 0:
                        detection_time = float(detections[0])
                        delay = float(detection_time - event_start)
                    else:
                        detection_time = np.nan
                        delay = np.nan

                rows.append(
                    {
                        "configuration": config_id,
                        "scenario": scenario,
                        "metric": metric_pretty_name(metric),
                        "window_size": w,
                        "stride": s,
                        "detection_time": detection_time,
                        "delay": delay,
                        "false_positives": false_positives,
                        "peak_intensity": peak_intensity,
                        "tau": tau,
                        "config_order": config_order.get(config_id, 99),
                        "scenario_order": SCENARIO_ORDER.get(str(scenario), 99),
                        "metric_order": METRIC_ORDER.get(metric, 99),
                    }
                )

    summary_df = pd.DataFrame(rows)
    if summary_df.empty:
        return summary_df

    return summary_df.sort_values(
        ["config_order", "scenario_order", "metric_order"]
    ).reset_index(drop=True)


def write_summary(summary_df: pd.DataFrame, output_file: Path) -> None:
    lines = [
        "Run Results Summary",
        "",
        "Rule: detection threshold tau = mean(stable |Delta H|) + 3 * std(stable |Delta H|)",
        f"Drift interval: t={DRIFT_START}..{DRIFT_END}",
        f"Shock event start: t={SHOCK_CENTER - (2 * SHOCK_WIDTH)}",
        "",
        "Columns: configuration | scenario | metric | window | stride | detection_time | delay | false_positives | peak_intensity",
        "",
    ]

    display_df = summary_df[
        [
            "configuration",
            "scenario",
            "metric",
            "window_size",
            "stride",
            "detection_time",
            "delay",
            "false_positives",
            "peak_intensity",
        ]
    ].copy()

    display_df["scenario"] = display_df["scenario"].map(scenario_pretty_name)
    display_df["detection_time"] = display_df["detection_time"].map(format_time)
    display_df["delay"] = display_df["delay"].map(format_time)
    display_df["false_positives"] = display_df["false_positives"].astype(int)
    display_df["peak_intensity"] = display_df["peak_intensity"].map(
        lambda value: f"{float(value):.6f}"
    )
    display_df = display_df.rename(
        columns={
            "window_size": "window",
            "false_positives": "false_pos",
        }
    )

    lines.append(display_df.to_string(index=False))
    lines.append("")

    output_file.write_text("\n".join(lines), encoding="utf-8")
    print(f"[OK] Report risultati salvato: {output_file}")


def main() -> None:
    ensure_directories()

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    required_columns = {
        "configuration",
        "scenario",
        "window_size",
        "stride",
        "t_center",
    }
    for metric in ENTROPY_METRICS:
        required_columns.add(metric_delta_column(metric))

    missing = required_columns - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Il file risultati non contiene le colonne richieste: {sorted(missing)}"
        )

    summary_df = build_summary(df, time_column="t_center")
    if summary_df.empty:
        raise RuntimeError("Nessun dato disponibile per esportare i risultati dei run.")

    write_summary(summary_df, OUTPUT_FILE)


if __name__ == "__main__":
    main()
