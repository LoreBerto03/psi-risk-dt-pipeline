import time
from typing import Optional

import pandas as pd
import requests


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

    raise RuntimeError(f"Servizio HTTP non raggiungibile: {url}. Ultimo errore: {last_error}")


def get_spark_session(master_url: str, app_name: str = "psi-risk-dt-pipeline"):
    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder
        .master(master_url)
        .appName(app_name)
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    return spark

def fetch_fuseki_points(base_url: str, dataset_name: str) -> pd.DataFrame:
    """
    Legge i dati reali da Fuseki.
    Si aspetta triple con questo schema logico:

    ?obs psi:scenario ?scenario ;
         psi:t        ?t ;
         psi:value    ?value .
    """
    query_url = f"{base_url}/{dataset_name}/sparql"

    sparql = """
    PREFIX psi: <http://example.org/psi-risk#>

    SELECT ?scenario ?t ?value
    WHERE {
      ?obs psi:scenario ?scenario ;
           psi:t ?t ;
           psi:value ?value .
    }
    ORDER BY ?scenario ?t
    """

    response = requests.get(
        query_url,
        params={"query": sparql},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30,
    )

    if response.status_code == 404:
        raise RuntimeError(
            f"Dataset Fuseki '{dataset_name}' non trovato su {base_url}. "
            f"Controlla che esista davvero e che contenga dati."
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
            f"Controlla predicati e struttura RDF."
        )

    df = pd.DataFrame(rows).sort_values(["scenario", "t"]).reset_index(drop=True)
    return df