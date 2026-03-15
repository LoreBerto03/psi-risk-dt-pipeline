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

from config import ensure_directories


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

    for scenario in scenarios:
        scenario_df = df[df["scenario"] == scenario].copy().sort_values("t")

        if scenario_df.empty:
            continue

        plt.figure(figsize=(12, 6))
        plt.plot(
            scenario_df["t"],
            scenario_df["value"],
        )
        plt.title(f"Signal / residual over time - {scenario}")
        plt.xlabel("t")
        plt.ylabel("Residual Δt")
        plt.grid(True)
        plt.tight_layout()

        output_file = figures_dir / f"signal_{sanitize_name(scenario)}.png"
        plt.savefig(output_file, dpi=150)
        plt.close()

        print(f"[OK] Grafico segnale salvato: {output_file}")


if __name__ == "__main__":
    main()