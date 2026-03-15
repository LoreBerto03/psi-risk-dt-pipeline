import time
from typing import Optional

import pandas as pd
import requests

from config import FUSEKI_ADMIN_USER, FUSEKI_ADMIN_PASSWORD


def get_fuseki_auth():
    return (FUSEKI_ADMIN_USER, FUSEKI_ADMIN_PASSWORD)


def wait_for_http(url: str, timeout_seconds: int = 60) -> None:
    start = time.time()
    last_error: Optional[Exception] = None

    while time.time() - start < timeout_seconds:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code < 500:
                return
        except Exception as exc:
            last_error = exc
        time.sleep(2)

    raise RuntimeError(
        f"Servizio HTTP non raggiungibile: {url}. Ultimo errore: {last_error}"
    )

def fetch_fuseki_points(base_url: str, dataset_name: str) -> pd.DataFrame:
    query_url = f"{base_url}/{dataset_name}/query"

    sparql = """
    PREFIX psi: <http://example.org/psi-risk#>

    SELECT ?scenario ?t ?value
    WHERE {
      ?obs a psi:Observation ;
           psi:scenario ?scenario ;
           psi:t ?t ;
           psi:value ?value .
    }
    ORDER BY ?scenario ?t
    """

    response = requests.post(
        query_url,
        data={"query": sparql},
        headers={"Accept": "application/sparql-results+json"},
        auth=get_fuseki_auth(),
        timeout=30,
    )

    if response.status_code == 404:
        raise RuntimeError(
            f"Dataset Fuseki '{dataset_name}' non trovato su {base_url}. "
            "Controlla che esista davvero e che contenga dati."
        )

    response.raise_for_status()

    payload = response.json()
    bindings = payload.get("results", {}).get("bindings", [])

    rows = []
    for item in bindings:
        rows.append(
            {
                "scenario": item["scenario"]["value"],
                "t": int(float(item["t"]["value"])),
                "value": float(item["value"]["value"]),
            }
        )

    if not rows:
        raise RuntimeError(
            f"Il dataset Fuseki '{dataset_name}' esiste, ma la query non ha restituito righe. "
            "Controlla predicati, tipo RDF e struttura dei dati caricati."
        )

    df = pd.DataFrame(rows).sort_values(["scenario", "t"]).reset_index(drop=True)
    return df