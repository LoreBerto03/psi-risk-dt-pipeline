#!/usr/bin/env bash
set -euo pipefail

COMPOSE_FILE="docker/docker-compose.yml"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$PROJECT_DIR"

cleanup() {
  echo
  echo "[CLEANUP] Arresto stack Docker..."
  docker compose -f "$COMPOSE_FILE" down
}

clear_generated_outputs() {
  find 05_Risultati/tables -type f \
    \( -name "*.csv" -o -name "*.ttl" \) -delete 2>/dev/null || true
  find 05_Risultati/figures -type f \
    \( -name "*.png" -o -name "*.txt" \) -delete 2>/dev/null || true
  find 05_Risultati/figures -mindepth 1 -maxdepth 1 -type d ! -name entropy -exec rm -rf {} + \
    2>/dev/null || true
  find 05_Risultati/tables -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + \
    2>/dev/null || true
}

prepare_output_layout() {
  clear_generated_outputs

  mkdir -p \
    05_Risultati/tables \
    05_Risultati/tables/final \
    05_Risultati/figures \
    05_Risultati/figures/entropy \
    05_Risultati/figures/final
}

trap cleanup EXIT

prepare_output_layout

echo "[1/8] Avvio servizi Docker..."
docker compose -f "$COMPOSE_FILE" up -d fuseki

echo "[2/8] Attesa Fuseki..."
until curl -fsS http://localhost:3030/\$/ping >/dev/null; do
  sleep 2
done
echo "[OK] Fuseki pronto"

echo "[3/8] Generazione dataset sintetico + upload su Fuseki..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 01_Generazione_dati/generate_and_upload_synthetic_to_fuseki.py

echo "[4/8] Calcolo sliding window + entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 03_Sliding_window/sliding_window.py

echo "[5/8] Generazione grafici entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/plot_entropy.py

echo "[6/8] Estrazione risultati dei run..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/export_run_results.py

echo "[7/8] Generazione pacchetto figure finale..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/build_final_figure_package.py

echo "[8/8] Generazione tabella finale results-ready..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/export_results_ready_table.py

echo "[OUTPUT] Output generati:"
echo
echo "[TABLES]"
find 05_Risultati/tables -maxdepth 2 -type f | sort || true
echo
echo "[FIGURES]"
find 05_Risultati/figures -maxdepth 3 -type f | sort || true

echo
echo "[OK] Pipeline completata"
