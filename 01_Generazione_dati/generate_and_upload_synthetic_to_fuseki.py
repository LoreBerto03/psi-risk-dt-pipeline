import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, XSD

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "Config"
UTILS_DIR = PROJECT_ROOT / "03_Sliding_window"

for p in [PROJECT_ROOT, CONFIG_DIR, UTILS_DIR]:
    if str(p) not in sys.path:
        sys.path.append(str(p))

from config import (
    SYNTHETIC_SEED,
    SYNTHETIC_POINTS_PER_SCENARIO,
    DRIFT_START,
    DRIFT_END,
    DRIFT_MAX,
    SHOCK_CENTER,
    SHOCK_WIDTH,
    SHOCK_AMPLITUDE,
    BASELINE_LEVEL,
    NOISE_STD,
    FUSEKI_BASE_URL,
    FUSEKI_DATASET,
    FUSEKI_ADMIN_USER,
    FUSEKI_ADMIN_PASSWORD,
    ensure_directories,
)
from docker_utils import wait_for_http

PSI = Namespace("http://example.org/psi-risk#")


def get_fuseki_auth():
    return (FUSEKI_ADMIN_USER, FUSEKI_ADMIN_PASSWORD)


def generate_synthetic_dataset() -> pd.DataFrame:
    rng = np.random.default_rng(SYNTHETIC_SEED)
    t = np.arange(SYNTHETIC_POINTS_PER_SCENARIO, dtype=int)

    stable_values = BASELINE_LEVEL + rng.normal(
        0.0, NOISE_STD, size=SYNTHETIC_POINTS_PER_SCENARIO
    )

    drift_component = np.zeros(SYNTHETIC_POINTS_PER_SCENARIO, dtype=float)
    drift_mask = (t >= DRIFT_START) & (t <= DRIFT_END)
    if drift_mask.sum() == 0:
        raise ValueError("Intervallo drift non valido: nessun punto selezionato.")

    drift_component[drift_mask] = np.linspace(0.0, DRIFT_MAX, drift_mask.sum())
    drift_component[t > DRIFT_END] = DRIFT_MAX

    drift_values = BASELINE_LEVEL + drift_component + rng.normal(
        0.0, NOISE_STD, size=SYNTHETIC_POINTS_PER_SCENARIO
    )

    shock_pulse = SHOCK_AMPLITUDE * np.exp(
        -0.5 * ((t - SHOCK_CENTER) / SHOCK_WIDTH) ** 2
    )
    shock_values = BASELINE_LEVEL + shock_pulse + rng.normal(
        0.0, NOISE_STD, size=SYNTHETIC_POINTS_PER_SCENARIO
    )

    frames = [
        pd.DataFrame({"scenario": "stable", "t": t, "value": stable_values}),
        pd.DataFrame({"scenario": "drift_gradual", "t": t, "value": drift_values}),
        pd.DataFrame({"scenario": "shock", "t": t, "value": shock_values}),
    ]

    return pd.concat(frames, ignore_index=True)


def dataframe_to_rdf(df: pd.DataFrame) -> Graph:
    g = Graph()
    g.bind("psi", PSI)

    for row in df.itertuples(index=False):
        scenario = str(row.scenario)
        t_value = int(row.t)
        value = float(row.value)

        point_uri = URIRef(f"{PSI}point/{scenario}/{t_value}")

        g.add((point_uri, RDF.type, PSI.Observation))
        g.add((point_uri, PSI.scenario, Literal(scenario, datatype=XSD.string)))
        g.add((point_uri, PSI.t, Literal(t_value, datatype=XSD.integer)))
        g.add((point_uri, PSI.value, Literal(value, datatype=XSD.double)))

    return g


def upload_graph_to_fuseki_default(graph: Graph) -> None:
    data_url = f"{FUSEKI_BASE_URL}/{FUSEKI_DATASET}/data?default"
    turtle_data = graph.serialize(format="turtle")

    response = requests.put(
        data_url,
        data=turtle_data.encode("utf-8"),
        headers={"Content-Type": "text/turtle; charset=utf-8"},
        auth=get_fuseki_auth(),
        timeout=120,
    )
    response.raise_for_status()


def save_debug_outputs(df: pd.DataFrame, graph: Graph) -> None:
    ensure_directories()

    tables_dir = PROJECT_ROOT / "05_Risultati" / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    df.to_csv(tables_dir / "synthetic_points_generated.csv", index=False)

    ttl_path = tables_dir / "synthetic_points_generated.ttl"
    graph.serialize(destination=str(ttl_path), format="turtle")


def main() -> None:
    print(f"[INFO] Attendo Fuseki su {FUSEKI_BASE_URL} ...")
    wait_for_http(f"{FUSEKI_BASE_URL}/$/ping", timeout_seconds=60)

    print("[INFO] Generazione dataset sintetico...")
    df = generate_synthetic_dataset()
    print(f"[INFO] Righe generate: {len(df)}")
    print(df.head())

    print("[INFO] Conversione in RDF...")
    graph = dataframe_to_rdf(df)
    print(f"[INFO] Triple generate: {len(graph)}")

    print("[INFO] Salvataggio output di debug...")
    save_debug_outputs(df, graph)

    print("[INFO] Upload dati sintetici su Fuseki...")
    upload_graph_to_fuseki_default(graph)

    print("[OK] Dataset sintetico caricato su Fuseki")


if __name__ == "__main__":
    main()