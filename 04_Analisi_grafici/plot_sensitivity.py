import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "Config"

for p in [PROJECT_ROOT, CONFIG_DIR]:
    if str(p) not in sys.path:
        sys.path.append(str(p))

from config import (
    ENTROPY_RESULT_FILE,
    DRIFT_START,
    DRIFT_END,
    SHOCK_CENTER,
    SHOCK_WIDTH,
    SENSITIVITY_TABLES_DIR,
    SENSITIVITY_FIGURES_DIR,
    get_configuration_id,
    ensure_directories,
)

SENSITIVITY_METRIC = os.getenv("SENSITIVITY_METRIC", "shannon").strip().lower()
THRESHOLD_STD_FACTOR = float(os.getenv("SENSITIVITY_STD_FACTOR", "3.0"))

COLOR_STRIDE = {
    1: "#1d4ed8",
    4: "#f59e0b",
    8: "#dc2626",
}


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
    if metric not in mapping:
        raise ValueError(f"Metrica non supportata: {metric}")
    return mapping[metric]


def metric_pretty_name(metric: str) -> str:
    mapping = {
        "shannon": "Shannon",
        "sample": "Sample",
        "permutation": "Permutation",
    }
    if metric not in mapping:
        raise ValueError(f"Metrica non supportata: {metric}")
    return mapping[metric]


def event_start_for_scenario(scenario: str) -> float | None:
    scenario = str(scenario).strip().lower()

    if scenario == "drift_gradual":
        return float(DRIFT_START)

    if scenario == "shock":
        return float(SHOCK_CENTER - (2 * SHOCK_WIDTH))

    return None


def sanitize_name(value: str) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def compute_tau_from_stable(stable_df: pd.DataFrame, delta_col: str) -> float:
    values = stable_df[delta_col].fillna(0.0).to_numpy(dtype=float)
    return float(values.mean() + THRESHOLD_STD_FACTOR * values.std(ddof=0))


def build_summary(df: pd.DataFrame, time_column: str, delta_col: str) -> pd.DataFrame:
    rows = []

    configs = (
        df[["window_size", "stride"]]
        .drop_duplicates()
        .sort_values(["window_size", "stride"])
        .itertuples(index=False)
    )

    for config in configs:
        w = int(config.window_size)
        s = int(config.stride)

        config_df = df[(df["window_size"] == w) & (df["stride"] == s)].copy()

        stable_df = (
            config_df[config_df["scenario"] == "stable"]
            .copy()
            .sort_values(time_column)
        )

        if stable_df.empty:
            continue

        tau = compute_tau_from_stable(stable_df, delta_col)

        for scenario in sorted(config_df["scenario"].dropna().unique().tolist()):
            scenario_df = (
                config_df[config_df["scenario"] == scenario]
                .copy()
                .sort_values(time_column)
            )

            signal = scenario_df[delta_col].fillna(0.0).to_numpy(dtype=float)
            times = scenario_df[time_column].to_numpy(dtype=float)

            if signal.size == 0:
                continue

            event_start = event_start_for_scenario(scenario)

            if event_start is None:
                # scenario stabile
                baseline_signal = signal
                fp_count = int(np.sum(signal > tau))
                fp_ratio = float(fp_count / len(signal)) if len(signal) > 0 else 0.0
                detection_time = np.nan
                detection_delay = np.nan
                false_negative_flag = 0
            else:
                pre_mask = times < event_start
                post_mask = times >= event_start

                baseline_signal = signal[pre_mask] if np.any(pre_mask) else signal

                fp_count = int(np.sum(signal[pre_mask] > tau)) if np.any(pre_mask) else 0
                fp_ratio = float(fp_count / np.sum(pre_mask)) if np.any(pre_mask) else 0.0

                post_times = times[post_mask]
                post_signal = signal[post_mask]

                detections = post_times[post_signal > tau]
                if detections.size > 0:
                    detection_time = float(detections[0])
                    detection_delay = float(detection_time - event_start)
                    false_negative_flag = 0
                else:
                    detection_time = np.nan
                    detection_delay = np.nan
                    false_negative_flag = 1

            noise_mean = float(np.mean(baseline_signal)) if baseline_signal.size > 0 else 0.0
            noise_std = float(np.std(baseline_signal, ddof=0)) if baseline_signal.size > 0 else 0.0

            rows.append(
                {
                    "metric": SENSITIVITY_METRIC,
                    "configuration": get_configuration_id(w, s) or "",
                    "scenario": scenario,
                    "window_size": w,
                    "stride": s,
                    "tau": float(tau),
                    "noise_mean": noise_mean,
                    "noise_std": noise_std,
                    "fp_count": int(fp_count),
                    "fp_ratio": float(fp_ratio),
                    "false_negative_flag": int(false_negative_flag),
                    "detection_time": detection_time,
                    "detection_delay": detection_delay,
                }
            )

    return pd.DataFrame(rows)


def plot_metric_vs_window(
    df: pd.DataFrame,
    scenario: str,
    value_column: str,
    ylabel: str,
    title: str,
    output_file: Path,
) -> None:
    plt.figure(figsize=(10, 6))

    scenario_df = (
        df[df["scenario"] == scenario]
        .copy()
        .sort_values(["stride", "window_size"])
    )

    available_strides = sorted(scenario_df["stride"].dropna().unique().tolist())

    for stride in available_strides:
        stride_df = (
            scenario_df[scenario_df["stride"] == stride]
            .copy()
            .sort_values("window_size")
        )

        if stride_df.empty:
            continue

        plt.plot(
            stride_df["window_size"],
            stride_df[value_column],
            marker="o",
            linewidth=2.2,
            color=COLOR_STRIDE.get(int(stride), "#374151"),
            label=f"stride={int(stride)}",
        )

    plt.title(title)
    plt.xlabel("Window size")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.25)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(output_file, dpi=160)
    plt.close()

    print(f"[OK] Grafico sensibilità salvato: {output_file}")


def refresh_combined_summary(output_tables_dir: Path) -> None:
    summary_files = sorted(
        path
        for path in output_tables_dir.glob("sensitivity_summary_*.csv")
        if path.name != "sensitivity_summary_all_metrics.csv"
    )

    if not summary_files:
        return

    frames = [pd.read_csv(path) for path in summary_files]
    combined_df = pd.concat(frames, ignore_index=True)
    combined_df = combined_df.sort_values(
        ["metric", "scenario", "window_size", "stride"]
    ).reset_index(drop=True)

    combined_file = output_tables_dir / "sensitivity_summary_all_metrics.csv"
    combined_df.to_csv(combined_file, index=False)
    print(f"[OK] Tabella sensitivity aggregata salvata: {combined_file}")


def main() -> None:
    ensure_directories()

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    delta_col = metric_delta_column(SENSITIVITY_METRIC)

    required_columns = {
        "scenario",
        "window_size",
        "stride",
        delta_col,
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Il file risultati non contiene le colonne richieste: {sorted(missing)}"
        )

    if "t_center" in df.columns:
        time_column = "t_center"
    elif "t_end" in df.columns:
        time_column = "t_end"
    else:
        raise RuntimeError("Il file risultati non contiene né 't_center' né 't_end'.")

    metric_slug = sanitize_name(SENSITIVITY_METRIC)
    metric_name = metric_pretty_name(SENSITIVITY_METRIC)

    output_tables_dir = SENSITIVITY_TABLES_DIR
    output_figures_dir = SENSITIVITY_FIGURES_DIR / metric_slug
    output_tables_dir.mkdir(parents=True, exist_ok=True)
    output_figures_dir.mkdir(parents=True, exist_ok=True)

    summary_df = build_summary(df, time_column=time_column, delta_col=delta_col)

    if summary_df.empty:
        raise RuntimeError("Nessun dato disponibile per costruire la sensitivity analysis.")

    summary_file = output_tables_dir / f"sensitivity_summary_{metric_slug}.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"[OK] Tabella sensitivity salvata: {summary_file}")
    refresh_combined_summary(output_tables_dir)

    plot_metric_vs_window(
        df=summary_df,
        scenario="stable",
        value_column="noise_std",
        ylabel="Noise std on stable",
        title=f"Sensitivity analysis - noise std ({metric_name})",
        output_file=output_figures_dir / f"sensitivity_noise_{metric_slug}.png",
    )

    plot_metric_vs_window(
        df=summary_df,
        scenario="stable",
        value_column="fp_ratio",
        ylabel="False positive ratio",
        title=f"Sensitivity analysis - false positives on stable ({metric_name})",
        output_file=output_figures_dir / f"sensitivity_fp_stable_{metric_slug}.png",
    )

    plot_metric_vs_window(
        df=summary_df,
        scenario="drift_gradual",
        value_column="detection_delay",
        ylabel="Detection delay",
        title=f"Sensitivity analysis - drift delay ({metric_name})",
        output_file=output_figures_dir / f"sensitivity_delay_drift_{metric_slug}.png",
    )

    plot_metric_vs_window(
        df=summary_df,
        scenario="shock",
        value_column="detection_delay",
        ylabel="Detection delay",
        title=f"Sensitivity analysis - shock delay ({metric_name})",
        output_file=output_figures_dir / f"sensitivity_delay_shock_{metric_slug}.png",
    )

    plot_metric_vs_window(
        df=summary_df,
        scenario="drift_gradual",
        value_column="false_negative_flag",
        ylabel="False negative flag",
        title=f"Sensitivity analysis - drift false negatives ({metric_name})",
        output_file=output_figures_dir / f"sensitivity_fn_drift_{metric_slug}.png",
    )

    plot_metric_vs_window(
        df=summary_df,
        scenario="shock",
        value_column="false_negative_flag",
        ylabel="False negative flag",
        title=f"Sensitivity analysis - shock false negatives ({metric_name})",
        output_file=output_figures_dir / f"sensitivity_fn_shock_{metric_slug}.png",
    )


if __name__ == "__main__":
    main()
