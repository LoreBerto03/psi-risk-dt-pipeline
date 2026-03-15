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
    DRIFT_START,
    DRIFT_END,
    SHOCK_CENTER,
    SHOCK_WIDTH,
    ensure_directories,
)

PLOT_SIGNAL_SMOOTH_POINTS = int(os.getenv("PLOT_SIGNAL_SMOOTH_POINTS", "25"))
PLOT_SIGNAL_SHOW_RAW = os.getenv("PLOT_SIGNAL_SHOW_RAW", "1") == "1"


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


def add_scenario_highlight(ax, scenario: str) -> None:
    scenario = str(scenario).strip().lower()

    if scenario == "drift_gradual":
        ax.axvspan(DRIFT_START, DRIFT_END, alpha=0.15, label="drift interval")
    elif scenario == "shock":
        half_width = SHOCK_WIDTH * 2
        ax.axvspan(
            SHOCK_CENTER - half_width,
            SHOCK_CENTER + half_width,
            alpha=0.15,
            label="shock interval",
        )


def scenario_pretty_name(scenario: str) -> str:
    mapping = {
        "stable": "Stable scenario",
        "drift_gradual": "Gradual drift scenario",
        "shock": "Shock scenario",
    }
    return mapping.get(str(scenario), str(scenario))


def main() -> None:
    ensure_directories()

    input_file = PROJECT_ROOT / "05_Risultati" / "tables" / "raw_points.csv"
    if not input_file.exists():
        raise FileNotFoundError(
            f"File non trovato: {input_file}\n"
            "Esegui prima 03_Sliding_window/sliding_window.py"
        )

    df = pd.read_csv(input_file)

    required_columns = {"scenario", "t", "value"}
    missing = required_columns - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Il file raw_points.csv non contiene le colonne richieste: {sorted(missing)}"
        )

    if df.empty:
        raise RuntimeError("Il file raw_points.csv è vuoto.")

    figures_dir = PROJECT_ROOT / "05_Risultati" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    scenarios = sorted(df["scenario"].dropna().unique().tolist())
    if not scenarios:
        raise RuntimeError("Nessuno scenario trovato in raw_points.csv")

    # scala y comune per tutti gli scenari
    global_y_min = float(df["value"].min())
    global_y_max = float(df["value"].max())

    if global_y_min == global_y_max:
        global_y_max = global_y_min + 1e-6

    padding = 0.05 * (global_y_max - global_y_min)
    y_min = global_y_min - padding
    y_max = global_y_max + padding

    for scenario in scenarios:
        scenario_df = df[df["scenario"] == scenario].copy().sort_values("t")

        if scenario_df.empty:
            continue

        x = scenario_df["t"]
        y_raw = scenario_df["value"]
        y_smooth = smooth_series(y_raw, PLOT_SIGNAL_SMOOTH_POINTS)

        plt.figure(figsize=(12, 6))

        if PLOT_SIGNAL_SHOW_RAW:
            plt.plot(
                x,
                y_raw,
                alpha=0.25,
                linewidth=0.8,
                label="raw signal",
            )

        plt.plot(
            x,
            y_smooth,
            linewidth=2.2,
            label=f"smoothed signal ({PLOT_SIGNAL_SMOOTH_POINTS} pts)",
        )

        add_scenario_highlight(plt.gca(), scenario)

        plt.title(f"{scenario_pretty_name(scenario)} – residual signal over time")
        plt.xlabel("time")
        plt.ylabel("Residual Δt")
        plt.ylim(y_min, y_max)
        plt.grid(True)
        plt.legend(loc="best")
        plt.tight_layout()

        output_file = figures_dir / f"signal_{sanitize_name(scenario)}.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"[OK] Grafico segnale salvato: {output_file}")


if __name__ == "__main__":
    main()