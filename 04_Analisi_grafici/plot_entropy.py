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
    ENTROPY_FIGURES_DIR,
    get_configuration_id,
    ensure_directories,
)

RAW_SHANNON = "#93c5fd"
RAW_SAMPLE = "#86efac"
RAW_PERM = "#d8b4fe"

SHANNON_COLOR = "#1d4ed8"
SAMPLE_COLOR = "#16a34a"
PERMUTATION_COLOR = "#7c3aed"

DRIFT_SPAN_COLOR = "#f59e0b"
SHOCK_SPAN_COLOR = "#ef4444"

PLOT_SMOOTH_POINTS = int(os.getenv("PLOT_SMOOTH_POINTS", "25"))
PLOT_SHOW_RAW = os.getenv("PLOT_SHOW_RAW", "1") == "1"
THRESHOLD_STD_FACTOR = float(os.getenv("SENSITIVITY_STD_FACTOR", "3.0"))


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


def smooth_series(series: pd.Series, points: int) -> pd.Series:
    if points <= 1:
        return series.copy()
    return series.rolling(points, center=True, min_periods=1).mean()


def compute_plot_limits(
    *series_list: pd.Series,
    min_padding: float = 1e-3,
) -> tuple[float, float]:
    combined = pd.concat(series_list, ignore_index=True).dropna()

    if combined.empty:
        return (0.0, 1.0)

    vmin = float(combined.min())
    vmax = float(combined.max())

    if vmin == vmax:
        vmax = vmin + min_padding

    padding = max(0.05 * (vmax - vmin), min_padding)
    return (max(0.0, vmin - padding), vmax + padding)


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


def compute_detection_time(
    scenario_df: pd.DataFrame,
    stable_df: pd.DataFrame,
    scenario: str,
    time_column: str,
    delta_col: str,
) -> float:
    event_start = event_start_for_scenario(scenario)
    if event_start is None:
        return float("nan")

    tau = compute_tau_from_stable(stable_df, delta_col)
    signal = scenario_df[delta_col].fillna(0.0).to_numpy(dtype=float)
    times = scenario_df[time_column].to_numpy(dtype=float)
    post_mask = times >= event_start
    post_times = times[post_mask]
    post_signal = signal[post_mask]
    detections = post_times[post_signal > tau]
    if detections.size == 0:
        return float("nan")
    return float(detections[0])


def main() -> None:
    ensure_directories()

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    required_columns = {
        "scenario",
        "window_size",
        "stride",
        "entropy_shannon",
        "entropy_sample",
        "entropy_permutation",
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
        raise RuntimeError(
            "Il file risultati non contiene né 't_center' né 't_end'."
        )

    figures_dir = ENTROPY_FIGURES_DIR
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

        for scenario in scenarios:
            scenario_df = (
                config_df[config_df["scenario"] == scenario]
                .copy()
                .sort_values(time_column)
            )

            if scenario_df.empty:
                continue

            x = scenario_df[time_column]

            shannon_raw = scenario_df["entropy_shannon"]
            sample_raw = scenario_df["entropy_sample"]
            permutation_raw = scenario_df["entropy_permutation"]

            shannon_smooth = smooth_series(shannon_raw, PLOT_SMOOTH_POINTS)
            sample_smooth = smooth_series(sample_raw, PLOT_SMOOTH_POINTS)
            permutation_smooth = smooth_series(permutation_raw, PLOT_SMOOTH_POINTS)
            y_min, y_max = compute_plot_limits(
                shannon_raw,
                sample_raw,
                permutation_raw,
            )

            plt.figure(figsize=(12, 6))

            if PLOT_SHOW_RAW:
                plt.plot(
                    x, shannon_raw, color=RAW_SHANNON, alpha=0.35,
                    linewidth=0.9, label="Shannon raw"
                )
                plt.plot(
                    x, sample_raw, color=RAW_SAMPLE, alpha=0.35,
                    linewidth=0.9, label="Sample raw"
                )
                plt.plot(
                    x, permutation_raw, color=RAW_PERM, alpha=0.35,
                    linewidth=0.9, label="Permutation raw"
                )

            plt.plot(
                x, shannon_smooth, color=SHANNON_COLOR,
                linewidth=2.4, label="Shannon"
            )
            plt.plot(
                x, sample_smooth, color=SAMPLE_COLOR,
                linewidth=2.4, label="Sample"
            )
            plt.plot(
                x, permutation_smooth, color=PERMUTATION_COLOR,
                linewidth=2.4, label="Permutation"
            )

            if scenario != "stable":
                shannon_detection_time = compute_detection_time(
                    scenario_df=scenario_df,
                    stable_df=stable_df,
                    scenario=scenario,
                    time_column=time_column,
                    delta_col="delta_h_shannon_abs",
                )
                sample_detection_time = compute_detection_time(
                    scenario_df=scenario_df,
                    stable_df=stable_df,
                    scenario=scenario,
                    time_column=time_column,
                    delta_col="delta_h_sample_abs",
                )
                permutation_detection_time = compute_detection_time(
                    scenario_df=scenario_df,
                    stable_df=stable_df,
                    scenario=scenario,
                    time_column=time_column,
                    delta_col="delta_h_permutation_abs",
                )

                for label, detection_time, color in [
                    ("Shannon detect", shannon_detection_time, SHANNON_COLOR),
                    ("Sample detect", sample_detection_time, SAMPLE_COLOR),
                    ("Permutation detect", permutation_detection_time, PERMUTATION_COLOR),
                ]:
                    if np.isfinite(detection_time):
                        plt.axvline(
                            detection_time,
                            color=color,
                            linestyle=":",
                            linewidth=1.5,
                            alpha=0.9,
                            label=f"{label} @ t={detection_time:.0f}",
                        )

            add_scenario_highlight(plt.gca(), scenario)

            config_title = (
                f"{configuration_label} - "
                if configuration_label
                else ""
            )
            title = (
                f"{scenario_pretty_name(scenario)} – "
                f"{config_title}W={selected_window}, stride={selected_stride}"
            )

            plt.title(title)
            plt.xlabel("time")
            plt.ylabel("Entropy H(t)")
            plt.ylim(y_min, y_max)
            plt.grid(True, alpha=0.25)
            plt.legend(loc="best")
            plt.tight_layout()

            output_file = figures_dir / (
                f"entropy_{sanitize_name(scenario)}"
                f"_w{selected_window}_s{selected_stride}.png"
            )
            plt.savefig(output_file, dpi=150)
            plt.close()

            total_plots += 1
            print(f"[OK] Grafico entropie salvato: {output_file}")

    print(f"[OK] Totale grafici entropia generati: {total_plots}")


if __name__ == "__main__":
    main()
