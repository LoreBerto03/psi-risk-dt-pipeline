import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
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
    ensure_directories,
)

RAW_RESIDUAL_COLOR = "#bfdbfe"
SMOOTH_RESIDUAL_COLOR = "#1d4ed8"

RAW_ENTROPY_COLOR = "#fde68a"
SMOOTH_ENTROPY_COLOR = "#d97706"

THRESHOLD_COLOR = "#111827"

DRIFT_SPAN_COLOR = "#f59e0b"
SHOCK_SPAN_COLOR = "#ef4444"

PLOT_SMOOTH_POINTS = int(os.getenv("PLOT_SMOOTH_POINTS", "25"))
PLOT_SHOW_RAW = os.getenv("PLOT_SHOW_RAW", "1") == "1"
BASELINE_ENTROPY_LABEL = "Shannon"


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


def main() -> None:
    ensure_directories()

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    required_columns = {
        "scenario",
        "window_size",
        "stride",
        "delta_h_abs",
        "abs_dt_max",
        "residual_threshold",
    }
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
            entropy_raw = scenario_df["delta_h_abs"].fillna(0.0)
            threshold = float(scenario_df["residual_threshold"].dropna().iloc[0])

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
                label=f"smoothed max |Δt| ({PLOT_SMOOTH_POINTS} pts)",
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
                    color=RAW_ENTROPY_COLOR,
                    alpha=0.45,
                    linewidth=0.9,
                    label=f"raw |ΔH {BASELINE_ENTROPY_LABEL}|",
                )

            ax2.plot(
                x,
                entropy_smooth,
                color=SMOOTH_ENTROPY_COLOR,
                linewidth=2.2,
                label=f"smoothed |ΔH {BASELINE_ENTROPY_LABEL}| ({PLOT_SMOOTH_POINTS} pts)",
            )
            add_scenario_highlight(ax2, scenario)
            ax2.set_xlabel("time")
            ax2.set_ylabel(f"{BASELINE_ENTROPY_LABEL} variation")
            ax2.grid(True, alpha=0.25)
            ax2.legend(loc="best")

            title = (
                f"Residual threshold vs {BASELINE_ENTROPY_LABEL} response – "
                f"{scenario_pretty_name(scenario)} – "
                f"W={selected_window}, stride={selected_stride}"
            )
            fig.suptitle(title)

            fig.tight_layout()

            output_file = figures_dir / (
                f"baseline_vs_entropy_{sanitize_name(scenario)}"
                f"_w{selected_window}_s{selected_stride}.png"
            )
            plt.savefig(output_file, dpi=150)
            plt.close(fig)

            total_plots += 1
            print(f"[OK] Grafico confronto salvato: {output_file}")

    print(f"[OK] Totale grafici baseline vs entropy generati: {total_plots}")


if __name__ == "__main__":
    main()
