from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Parametri analisi
EXPERIMENT_CONFIGS = (
    {
        "id": "C1",
        "window_size": 128,
        "stride": 1,
        "isolated_variable": "reference",
        "expected_effect": "Configurazione di riferimento.",
    },
    {
        "id": "C2",
        "window_size": 64,
        "stride": 1,
        "isolated_variable": "window",
        "expected_effect": "Finestra piccola: alta reattivita', minore stabilita'.",
    },
    {
        "id": "C3",
        "window_size": 256,
        "stride": 1,
        "isolated_variable": "window",
        "expected_effect": "Finestra grande: alta stabilita', maggiore ritardo.",
    },
    {
        "id": "C4",
        "window_size": 128,
        "stride": 4,
        "isolated_variable": "stride",
        "expected_effect": "Stride medio: test sulla frequenza di aggiornamento.",
    },
    {
        "id": "C5",
        "window_size": 128,
        "stride": 8,
        "isolated_variable": "stride",
        "expected_effect": "Stride ampio: minor costo computazionale, minor dettaglio.",
    },
)

REFERENCE_CONFIGURATION_ID = "C1"
PHASE2_CONFIGURATION_IDS = tuple(
    config["id"]
    for config in EXPERIMENT_CONFIGS
    if config["id"] != REFERENCE_CONFIGURATION_ID
)

WINDOW_SIZES = sorted({int(config["window_size"]) for config in EXPERIMENT_CONFIGS})
STRIDES = sorted({int(config["stride"]) for config in EXPERIMENT_CONFIGS})
CONFIGURATION_ID_BY_PAIR = {
    (int(config["window_size"]), int(config["stride"])): str(config["id"])
    for config in EXPERIMENT_CONFIGS
}
ENTROPY_BINS = 16

DEFAULT_WINDOW_SIZE = 128
DEFAULT_STRIDE = 1

# Dataset sintetico
SYNTHETIC_SEED = 42
SYNTHETIC_POINTS_PER_SCENARIO = 1000

DRIFT_START = 333
DRIFT_END = 667
DRIFT_MAX = 2.5

SHOCK_CENTER = 500
SHOCK_WIDTH = 8
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
ENTROPY_METRICS = ("shannon", "sample", "permutation")
SENSITIVITY_TABLES_DIR = TABLES_DIR / "sensitivity"
SENSITIVITY_FIGURES_DIR = FIGURES_DIR / "sensitivity"
SENSITIVITY_METRICS = ENTROPY_METRICS

ENTROPY_RESULT_FILE = TABLES_DIR / "entropy_final.csv"
FINAL_FIGURE_FILE = FIGURES_DIR / "grafico_final.png"


def get_configuration_id(window_size: int, stride: int) -> str | None:
    return CONFIGURATION_ID_BY_PAIR.get((int(window_size), int(stride)))


def iter_experiment_configurations(include_reference: bool = True):
    if include_reference:
        return EXPERIMENT_CONFIGS

    return tuple(
        config
        for config in EXPERIMENT_CONFIGS
        if config["id"] != REFERENCE_CONFIGURATION_ID
    )


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
    paths.extend(BASELINE_VS_ENTROPY_FIGURES_DIR / metric for metric in ENTROPY_METRICS)
    paths.extend(SENSITIVITY_FIGURES_DIR / metric for metric in SENSITIVITY_METRICS)

    for path in paths:
        path.mkdir(parents=True, exist_ok=True)
