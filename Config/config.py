from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Parametri analisi
WINDOW_SIZES = [64, 128, 256]
STRIDES = [1, 4, 8]
ENTROPY_BINS = 16

DEFAULT_WINDOW_SIZE = 128
DEFAULT_STRIDE = 1

# Dataset sintetico
SYNTHETIC_SEED = 42
SYNTHETIC_POINTS_PER_SCENARIO = 3000

DRIFT_START = 1000
DRIFT_END = 2000
DRIFT_MAX = 2.5

SHOCK_CENTER = 1500
SHOCK_WIDTH = 25
SHOCK_AMPLITUDE = 4.0

BASELINE_LEVEL = 0.0
NOISE_STD = 0.15

# Fuseki
FUSEKI_BASE_URL = os.getenv("FUSEKI_BASE_URL", "http://fuseki:3030")
FUSEKI_DATASET = os.getenv("FUSEKI_DATASET", "psi-risk")
FUSEKI_ADMIN_USER = os.getenv("FUSEKI_ADMIN_USER", "admin")
FUSEKI_ADMIN_PASSWORD = os.getenv("FUSEKI_ADMIN_PASSWORD", "")

# Output
RESULTS_DIR = PROJECT_ROOT / "05_Risultati"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"
SIGNAL_FIGURES_DIR = FIGURES_DIR / "signal"
ENTROPY_FIGURES_DIR = FIGURES_DIR / "entropy"
BASELINE_VS_ENTROPY_FIGURES_DIR = FIGURES_DIR / "baseline_vs_entropy"
SENSITIVITY_TABLES_DIR = TABLES_DIR / "sensitivity"
SENSITIVITY_FIGURES_DIR = FIGURES_DIR / "sensitivity"
SENSITIVITY_METRICS = ("shannon", "sample", "permutation")

ENTROPY_RESULT_FILE = TABLES_DIR / "entropy_final.csv"
FINAL_FIGURE_FILE = FIGURES_DIR / "grafico_final.png"

def ensure_directories() -> None:
    paths = [
        TABLES_DIR,
        FIGURES_DIR,
        SIGNAL_FIGURES_DIR,
        ENTROPY_FIGURES_DIR,
        BASELINE_VS_ENTROPY_FIGURES_DIR,
        SENSITIVITY_TABLES_DIR,
        SENSITIVITY_FIGURES_DIR,
    ]
    paths.extend(SENSITIVITY_FIGURES_DIR / metric for metric in SENSITIVITY_METRICS)

    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
