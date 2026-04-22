#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.yml"
RESULTS_DIR="$PROJECT_DIR/results"

cd "$PROJECT_DIR"

cleanup() {
  echo
  echo "[CLEANUP] Arresto stack Docker..."
  docker compose -f "$COMPOSE_FILE" down
}

clear_generated_outputs() {
  find "$RESULTS_DIR/tables" -type f \
    \( -name "*.csv" -o -name "*.ttl" \) -delete 2>/dev/null || true
  find "$RESULTS_DIR/figures" -type f \
    \( -name "*.png" -o -name "*.txt" \) -delete 2>/dev/null || true
  find "$RESULTS_DIR/figures" -mindepth 1 -maxdepth 1 -type d ! -name entropy -exec rm -rf {} + \
    2>/dev/null || true
  find "$RESULTS_DIR/tables" -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} + \
    2>/dev/null || true
}

prepare_output_layout() {
  clear_generated_outputs

  mkdir -p \
    "$RESULTS_DIR/tables" \
    "$RESULTS_DIR/tables/final" \
    "$RESULTS_DIR/figures" \
    "$RESULTS_DIR/figures/entropy" \
    "$RESULTS_DIR/figures/final"
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
docker compose -f "$COMPOSE_FILE" run --rm pipeline python src/data_generation/generate_and_upload_synthetic_to_fuseki.py

echo "[4/8] Calcolo sliding window + entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python src/sliding_window/sliding_window.py

echo "[5/8] Generazione grafici entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python src/analysis/plot_entropy.py

echo "[6/8] Estrazione risultati dei run..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python src/analysis/export_run_results.py

echo "[7/8] Generazione pacchetto figure finale..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python src/analysis/build_final_figure_package.py

echo "[8/8] Generazione tabella finale results-ready..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python src/analysis/export_results_ready_table.py

echo "[OUTPUT] Output generati:"
echo
echo "[TABLES]"
find "$RESULTS_DIR/tables" -maxdepth 2 -type f | sort || true
echo
echo "[FIGURES]"
find "$RESULTS_DIR/figures" -maxdepth 3 -type f | sort || true

echo
echo "[OK] Pipeline completata"
