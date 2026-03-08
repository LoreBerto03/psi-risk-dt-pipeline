from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Parametri analisi
WINDOW_SIZES = [50, 100, 200]
STEP = 1
ENTROPY_BINS = 16

# Docker / servizi
USE_SPARK = os.getenv("USE_SPARK", "1") == "1"
SPARK_MASTER_URL = os.getenv("SPARK_MASTER_URL", "spark://spark:7077")

USE_FUSEKI = os.getenv("USE_FUSEKI", "1") == "1"
FUSEKI_BASE_URL = os.getenv("FUSEKI_BASE_URL", "http://fuseki:3030")
FUSEKI_DATASET = os.getenv("FUSEKI_DATASET", "psi-risk")

# Sorgente dati reale
DATA_SOURCE = os.getenv("DATA_SOURCE", "fuseki")

# Output finali
RESULTS_DIR = PROJECT_ROOT / "05_Risultati"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"

ENTROPY_RESULT_FILE = TABLES_DIR / "entropy_final.csv"
FINAL_FIGURE_FILE = FIGURES_DIR / "grafico_finale.png"


def ensure_directories() -> None:
    for path in [TABLES_DIR, FIGURES_DIR]:
        path.mkdir(parents=True, exist_ok=True)