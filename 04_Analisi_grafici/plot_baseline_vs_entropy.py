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
    ensure_directories,
)

PLOT_WINDOW_SIZE = int(os.getenv("PLOT_WINDOW_SIZE", str(DEFAULT_WINDOW_SIZE)))
PLOT_STRIDE = int(os.getenv("PLOT_STRIDE", str(DEFAULT_STRIDE)))


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


def main() -> None:
    ensure_directories()

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    required_columns = {
        "scenario",
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

    for scenario in scenarios:
        scenario_df = (
            df[df["scenario"] == scenario]
            .copy()
            .sort_values(time_column)
        )

        if scenario_df.empty:
            continue

        threshold = float(scenario_df["residual_threshold"].dropna().iloc[0])

        fig, ax1 = plt.subplots(figsize=(12, 6))

        ax1.plot(
            scenario_df[time_column],
            scenario_df["abs_dt_max"],
            label="max |Δt| in window",
        )
        ax1.axhline(
            threshold,
            linestyle="--",
            label="baseline threshold",
        )
        ax1.set_xlabel(time_column)
        ax1.set_ylabel("Residual magnitude")
        ax1.grid(True)

        ax2 = ax1.twinx()
        ax2.plot(
            scenario_df[time_column],
            scenario_df["delta_h_abs"],
            label="|ΔH|",
        )
        ax2.set_ylabel("Entropy variation")

        title = f"Baseline vs entropy variation - {scenario}"
        if selected_window is not None:
            title += f" - window size {selected_window}"
        if selected_stride is not None:
            title += f" - stride {selected_stride}"
        plt.title(title)

        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="best")

        fig.tight_layout()

        suffix = ""
        if selected_window is not None:
            suffix += f"_w{selected_window}"
        if selected_stride is not None:
            suffix += f"_s{selected_stride}"

        output_file = figures_dir / f"baseline_vs_entropy_{sanitize_name(scenario)}{suffix}.png"
        plt.savefig(output_file, dpi=150)
        plt.close(fig)

        print(f"[OK] Grafico confronto salvato: {output_file}")


if __name__ == "__main__":
    main()