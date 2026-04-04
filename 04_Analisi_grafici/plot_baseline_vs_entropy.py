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
    BASELINE_VS_ENTROPY_FIGURES_DIR,
    ENTROPY_METRICS,
    get_configuration_id,
    ensure_directories,
)

RAW_RESIDUAL_COLOR = "#bfdbfe"
SMOOTH_RESIDUAL_COLOR = "#1d4ed8"

THRESHOLD_COLOR = "#111827"
DETECTION_COLOR = "#dc2626"

DRIFT_SPAN_COLOR = "#f59e0b"
SHOCK_SPAN_COLOR = "#ef4444"

PLOT_SMOOTH_POINTS = int(os.getenv("PLOT_SMOOTH_POINTS", "25"))
PLOT_SHOW_RAW = os.getenv("PLOT_SHOW_RAW", "1") == "1"
THRESHOLD_STD_FACTOR = float(os.getenv("SENSITIVITY_STD_FACTOR", "3.0"))

ENTROPY_PLOT_CONFIG = {
    "shannon": {
        "label": "Shannon",
        "delta_column": "delta_h_shannon_abs",
        "raw_color": "#93c5fd",
        "smooth_color": "#1d4ed8",
        "threshold_color": "#1e3a8a",
    },
    "sample": {
        "label": "Sample",
        "delta_column": "delta_h_sample_abs",
        "raw_color": "#86efac",
        "smooth_color": "#16a34a",
        "threshold_color": "#166534",
    },
    "permutation": {
        "label": "Permutation",
        "delta_column": "delta_h_permutation_abs",
        "raw_color": "#d8b4fe",
        "smooth_color": "#7c3aed",
        "threshold_color": "#5b21b6",
    },
}


def find_input_file() -> Path:
    candidates = [
        ENTROPY_RESULT_FILE,
        PROJECT_ROOT / "05_Risultati" / "tables" / "entropy_final.csv",
        PROJECT_ROOT / "05_Risultati" / "tables" / "entropy_over_time.csv",
        PROJECT_ROOT / "03_Sliding_window" / "outputs" / "entropy_over_time.csv",
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


def sanitize_name(value: str) -> str:
    return (
        str(value)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def add_scenario_highlight(ax, scenario: str) -> None:
    scenario = str(scenario).strip().lower()

    if scenario == "drift_gradual":
        ax.axvspan(
            DRIFT_START,
            DRIFT_END,
            color=DRIFT_SPAN_COLOR,
            alpha=0.18,
            label="drift interval",
        )
    elif scenario == "shock":
        half_width = SHOCK_WIDTH * 2
        ax.axvspan(
            SHOCK_CENTER - half_width,
            SHOCK_CENTER + half_width,
            color=SHOCK_SPAN_COLOR,
            alpha=0.18,
            label="shock interval",
        )


def smooth_series(series: pd.Series, points: int, mode: str = "mean") -> pd.Series:
    if points <= 1:
        return series.copy()

    if mode == "median":
        return series.rolling(points, center=True, min_periods=1).median()

    return series.rolling(points, center=True, min_periods=1).mean()


def scenario_pretty_name(scenario: str) -> str:
    mapping = {
        "stable": "Stable scenario",
        "drift_gradual": "Gradual drift scenario",
        "shock": "Shock scenario",
    }
    return mapping.get(str(scenario), str(scenario))


def resolve_configuration_label(
    config_df: pd.DataFrame,
    selected_window: int,
    selected_stride: int,
) -> str:
    if "configuration" in config_df.columns:
        values = config_df["configuration"].dropna().astype(str).str.strip()
        if not values.empty:
            return values.iloc[0]

    return get_configuration_id(selected_window, selected_stride) or ""


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


def compute_detection_stats(
    scenario_df: pd.DataFrame,
    stable_df: pd.DataFrame,
    scenario: str,
    time_column: str,
    delta_col: str,
) -> dict:
    tau = compute_tau_from_stable(stable_df, delta_col)
    signal = scenario_df[delta_col].fillna(0.0).to_numpy(dtype=float)
    times = scenario_df[time_column].to_numpy(dtype=float)
    event_start = event_start_for_scenario(scenario)

    if signal.size == 0:
        return {
            "tau": tau,
            "detection_time": np.nan,
            "detection_delay": np.nan,
            "false_negative_flag": int(event_start is not None),
        }

    if event_start is None:
        return {
            "tau": tau,
            "detection_time": np.nan,
            "detection_delay": np.nan,
            "false_negative_flag": 0,
        }

    post_mask = times >= event_start
    post_times = times[post_mask]
    post_signal = signal[post_mask]
    detections = post_times[post_signal > tau]

    if detections.size == 0:
        return {
            "tau": tau,
            "detection_time": np.nan,
            "detection_delay": np.nan,
            "false_negative_flag": 1,
        }

    detection_time = float(detections[0])
    return {
        "tau": tau,
        "detection_time": detection_time,
        "detection_delay": float(detection_time - event_start),
        "false_negative_flag": 0,
    }


def main() -> None:
    ensure_directories()

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    required_columns = {
        "scenario",
        "window_size",
        "stride",
        "abs_dt_max",
        "residual_threshold",
    }
    required_columns.update(
        ENTROPY_PLOT_CONFIG[metric]["delta_column"] for metric in ENTROPY_METRICS
    )
    missing = required_columns - set(df.columns)
    if missing:
        raise RuntimeError(
            "Il file risultati non contiene le colonne richieste per il confronto: "
            f"{sorted(missing)}"
        )

    if "t_center" in df.columns:
        time_column = "t_center"
    elif "t_end" in df.columns:
        time_column = "t_end"
    else:
        raise RuntimeError(
            "Il file risultati non contiene né 't_center' né 't_end'."
        )

    figures_dir = BASELINE_VS_ENTROPY_FIGURES_DIR
    figures_dir.mkdir(parents=True, exist_ok=True)

    scenarios = sorted(df["scenario"].dropna().unique().tolist())
    if not scenarios:
        raise RuntimeError("Nessuno scenario trovato nei dati.")

    configs = (
        df[["window_size", "stride"]]
        .drop_duplicates()
        .sort_values(["window_size", "stride"])
        .itertuples(index=False)
    )

    total_plots = 0

    for config in configs:
        selected_window = int(config.window_size)
        selected_stride = int(config.stride)

        config_df = df[
            (df["window_size"] == selected_window) &
            (df["stride"] == selected_stride)
        ].copy()
        configuration_label = resolve_configuration_label(
            config_df=config_df,
            selected_window=selected_window,
            selected_stride=selected_stride,
        )
        stable_df = (
            config_df[config_df["scenario"] == "stable"]
            .copy()
            .sort_values(time_column)
        )

        if stable_df.empty:
            continue

        for metric in ENTROPY_METRICS:
            metric_config = ENTROPY_PLOT_CONFIG[metric]
            metric_label = metric_config["label"]
            delta_col = metric_config["delta_column"]
            metric_figures_dir = figures_dir / metric
            metric_figures_dir.mkdir(parents=True, exist_ok=True)

            for scenario in scenarios:
                scenario_df = (
                    config_df[config_df["scenario"] == scenario]
                    .copy()
                    .sort_values(time_column)
                )

                if scenario_df.empty:
                    continue

                x = scenario_df[time_column]
                residual_raw = scenario_df["abs_dt_max"]
                entropy_raw = scenario_df[delta_col].fillna(0.0)
                threshold = float(scenario_df["residual_threshold"].dropna().iloc[0])
                detection_stats = compute_detection_stats(
                    scenario_df=scenario_df,
                    stable_df=stable_df,
                    scenario=scenario,
                    time_column=time_column,
                    delta_col=delta_col,
                )
                tau = float(detection_stats["tau"])
                detection_time = detection_stats["detection_time"]
                detection_delay = detection_stats["detection_delay"]

                residual_smooth = smooth_series(
                    residual_raw, points=PLOT_SMOOTH_POINTS, mode="median"
                )
                entropy_smooth = smooth_series(
                    entropy_raw, points=PLOT_SMOOTH_POINTS, mode="mean"
                )

                fig, (ax1, ax2) = plt.subplots(
                    2,
                    1,
                    figsize=(12, 8),
                    sharex=True,
                    gridspec_kw={"height_ratios": [2, 1]},
                )

                if PLOT_SHOW_RAW:
                    ax1.plot(
                        x,
                        residual_raw,
                        color=RAW_RESIDUAL_COLOR,
                        alpha=0.45,
                        linewidth=0.9,
                        label="raw max |Δt|",
                    )

                ax1.plot(
                    x,
                    residual_smooth,
                    color=SMOOTH_RESIDUAL_COLOR,
                    linewidth=2.2,
                    label="smoothed max |Δt|",
                )
                ax1.axhline(
                    threshold,
                    color=THRESHOLD_COLOR,
                    linestyle="--",
                    linewidth=1.6,
                    label="baseline threshold",
                )
                add_scenario_highlight(ax1, scenario)
                ax1.set_ylabel("Residual magnitude")
                ax1.grid(True, alpha=0.25)
                ax1.legend(loc="best")

                if PLOT_SHOW_RAW:
                    ax2.plot(
                        x,
                        entropy_raw,
                        color=metric_config["raw_color"],
                        alpha=0.45,
                        linewidth=0.9,
                        label=f"raw |ΔH {metric_label}|",
                    )

                ax2.plot(
                    x,
                    entropy_smooth,
                    color=metric_config["smooth_color"],
                    linewidth=2.2,
                    label=f"smoothed |ΔH {metric_label}|",
                )
                ax2.axhline(
                    tau,
                    color=metric_config["threshold_color"],
                    linestyle="--",
                    linewidth=1.6,
                    label=f"tau on |ΔH {metric_label}|",
                )

                if np.isfinite(detection_time):
                    detection_mask = (
                        (scenario_df[time_column] >= detection_time) &
                        (entropy_raw > tau)
                    )
                    detection_rows = scenario_df[detection_mask]
                    detection_value = (
                        float(entropy_raw.loc[detection_rows.index[0]])
                        if not detection_rows.empty
                        else tau
                    )

                    ax1.axvline(
                        detection_time,
                        color=DETECTION_COLOR,
                        linestyle=":",
                        linewidth=1.8,
                        label=f"first detection @ t={detection_time:.0f}",
                    )
                    ax2.axvline(
                        detection_time,
                        color=DETECTION_COLOR,
                        linestyle=":",
                        linewidth=1.8,
                        label=f"first detection @ t={detection_time:.0f}",
                    )
                    ax2.scatter(
                        [detection_time],
                        [detection_value],
                        color=DETECTION_COLOR,
                        s=34,
                        zorder=5,
                    )
                    ax2.annotate(
                        f"detect +{detection_delay:.0f}",
                        xy=(detection_time, detection_value),
                        xytext=(8, 8),
                        textcoords="offset points",
                        color=DETECTION_COLOR,
                        fontsize=9,
                    )

                add_scenario_highlight(ax2, scenario)
                ax2.set_xlabel("time")
                ax2.set_ylabel(f"{metric_label} variation")
                ax2.grid(True, alpha=0.25)
                ax2.legend(loc="best")

                title = (
                    f"Residual threshold vs {metric_label} response – "
                    f"{scenario_pretty_name(scenario)} – "
                    f"{configuration_label + ' - ' if configuration_label else ''}"
                    f"W={selected_window}, stride={selected_stride}"
                )
                fig.suptitle(title)

                fig.tight_layout()

                output_file = metric_figures_dir / (
                    f"baseline_vs_entropy_{metric}_{sanitize_name(scenario)}"
                    f"_w{selected_window}_s{selected_stride}.png"
                )
                plt.savefig(output_file, dpi=150)
                plt.close(fig)

                total_plots += 1
                print(f"[OK] Grafico confronto salvato: {output_file}")

    print(f"[OK] Totale grafici baseline vs entropy generati: {total_plots}")


if __name__ == "__main__":
    main()
