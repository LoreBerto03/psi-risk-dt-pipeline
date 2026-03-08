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

from config import ENTROPY_RESULT_FILE, ensure_directories

PLOT_WINDOW_SIZE = int(os.getenv("PLOT_WINDOW_SIZE", "100"))


def find_input_file() -> Path:
    candidates = [
        ENTROPY_RESULT_FILE,
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

    required_columns = {"scenario", "t_end", "entropy_shannon"}
    missing = required_columns - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Il file risultati non contiene le colonne richieste: {sorted(missing)}"
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

    if df.empty:
        raise RuntimeError("Nessun dato disponibile per generare i grafici.")

    figures_dir = PROJECT_ROOT / "05_Risultati" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    scenarios = sorted(df["scenario"].dropna().unique().tolist())
    if not scenarios:
        raise RuntimeError("Nessuno scenario trovato nei dati.")

    for scenario in scenarios:
        scenario_df = df[df["scenario"] == scenario].copy()

        if scenario_df.empty:
            continue

        plt.figure(figsize=(12, 6))
        plt.plot(
            scenario_df["t_end"],
            scenario_df["entropy_shannon"],
        )

        title = f"Entropy over time - {scenario}"
        if selected_window is not None:
            title += f" - window size {selected_window}"

        plt.title(title)
        plt.xlabel("t_end")
        plt.ylabel("Shannon entropy")
        plt.grid(True)
        plt.tight_layout()

        output_file = figures_dir / f"entropy_{sanitize_name(scenario)}.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"[OK] Grafico salvato: {output_file}")


if __name__ == "__main__":
    main()