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
    DEFAULT_WINDOW_SIZE,
    DEFAULT_STRIDE,
    DRIFT_START,
    DRIFT_END,
    SHOCK_CENTER,
    SHOCK_WIDTH,
    ensure_directories,
)

PLOT_WINDOW_SIZE = int(os.getenv("PLOT_WINDOW_SIZE", str(DEFAULT_WINDOW_SIZE)))
PLOT_STRIDE = int(os.getenv("PLOT_STRIDE", str(DEFAULT_STRIDE)))
PLOT_SMOOTH_POINTS = int(os.getenv("PLOT_SMOOTH_POINTS", "25"))
PLOT_SHOW_RAW = os.getenv("PLOT_SHOW_RAW", "1") == "1"


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

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    required_columns = {"scenario", "entropy_shannon"}
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

    selected_window = None
    if "window_size" in df.columns:
        available_windows = sorted(df["window_size"].dropna().unique().tolist())

        if not available_windows:
            raise RuntimeError(
                "La colonna 'window_size' esiste ma non contiene valori validi."
            )

        if PLOT_WINDOW_SIZE in available_windows:
            selected_window = PLOT_WINDOW_SIZE
        else:
            selected_window = available_windows[0]
            print(
                f"[WARN] window_size={PLOT_WINDOW_SIZE} non presente. "
                f"Uso window_size={selected_window}"
            )

        df = df[df["window_size"] == selected_window].copy()

    selected_stride = None
    if "stride" in df.columns:
        available_strides = sorted(df["stride"].dropna().unique().tolist())

        if not available_strides:
            raise RuntimeError(
                "La colonna 'stride' esiste ma non contiene valori validi."
            )

        if PLOT_STRIDE in available_strides:
            selected_stride = PLOT_STRIDE
        else:
            selected_stride = available_strides[0]
            print(
                f"[WARN] stride={PLOT_STRIDE} non presente. "
                f"Uso stride={selected_stride}"
            )

        df = df[df["stride"] == selected_stride].copy()

    if df.empty:
        raise RuntimeError("Nessun dato disponibile per generare i grafici.")

    figures_dir = PROJECT_ROOT / "05_Risultati" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    scenarios = sorted(df["scenario"].dropna().unique().tolist())
    if not scenarios:
        raise RuntimeError("Nessuno scenario trovato nei dati.")

    # scala y comune per tutti gli scenari
    global_y_min = float(df["entropy_shannon"].min())
    global_y_max = float(df["entropy_shannon"].max())

    if global_y_min == global_y_max:
        global_y_max = global_y_min + 1e-6

    padding = 0.05 * (global_y_max - global_y_min)
    y_min = global_y_min - padding
    y_max = global_y_max + padding

    for scenario in scenarios:
        scenario_df = (
            df[df["scenario"] == scenario]
            .copy()
            .sort_values(time_column)
        )

        if scenario_df.empty:
            continue

        x = scenario_df[time_column]
        y_raw = scenario_df["entropy_shannon"]
        y_smooth = smooth_series(y_raw, PLOT_SMOOTH_POINTS)

        plt.figure(figsize=(12, 6))

        if PLOT_SHOW_RAW:
            plt.plot(
                x,
                y_raw,
                alpha=0.25,
                linewidth=0.9,
                label="raw H(t)",
            )

        plt.plot(
            x,
            y_smooth,
            linewidth=2.2,
            label=f"smoothed H(t) ({PLOT_SMOOTH_POINTS} pts)",
        )

        add_scenario_highlight(plt.gca(), scenario)

        title = scenario_pretty_name(scenario)
        if selected_window is not None:
            title += f" – window {selected_window}"
        if selected_stride is not None:
            title += f", stride {selected_stride}"

        plt.title(title)
        plt.xlabel("time")
        plt.ylabel("Shannon entropy H(t)")
        plt.ylim(y_min, y_max)
        plt.grid(True)
        plt.legend(loc="best")
        plt.tight_layout()

        suffix = ""
        if selected_window is not None:
            suffix += f"_w{selected_window}"
        if selected_stride is not None:
            suffix += f"_s{selected_stride}"

        output_file = figures_dir / f"entropy_{sanitize_name(scenario)}{suffix}.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"[OK] Grafico entropia salvato: {output_file}")


if __name__ == "__main__":
    main()