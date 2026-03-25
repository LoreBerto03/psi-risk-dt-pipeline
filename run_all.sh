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

move_existing_outputs() {
  local search_dir="$1"
  local pattern="$2"
  local target_dir="$3"

  mkdir -p "$target_dir"

  while IFS= read -r -d '' file; do
    mv -n "$file" "$target_dir"/
  done < <(find "$search_dir" -maxdepth 1 -type f -name "$pattern" -print0)
}

prepare_output_layout() {
  mkdir -p \
    05_Risultati/tables \
    05_Risultati/tables/sensitivity \
    05_Risultati/figures \
    05_Risultati/figures/signal \
    05_Risultati/figures/entropy \
    05_Risultati/figures/baseline_vs_entropy \
    05_Risultati/figures/sensitivity/shannon \
    05_Risultati/figures/sensitivity/sample \
    05_Risultati/figures/sensitivity/permutation

  move_existing_outputs "05_Risultati/figures" "signal_*.png" "05_Risultati/figures/signal"
  move_existing_outputs "05_Risultati/figures" "entropy_*.png" "05_Risultati/figures/entropy"
  move_existing_outputs "05_Risultati/figures" "baseline_vs_entropy_*.png" "05_Risultati/figures/baseline_vs_entropy"
  move_existing_outputs "05_Risultati/figures" "sensitivity_*_shannon.png" "05_Risultati/figures/sensitivity/shannon"
  move_existing_outputs "05_Risultati/figures" "sensitivity_*_sample.png" "05_Risultati/figures/sensitivity/sample"
  move_existing_outputs "05_Risultati/figures" "sensitivity_*_permutation.png" "05_Risultati/figures/sensitivity/permutation"
  move_existing_outputs "05_Risultati/tables" "sensitivity_summary_*.csv" "05_Risultati/tables/sensitivity"
}

trap cleanup EXIT

prepare_output_layout

echo "[1/9] Avvio servizi Docker..."
docker compose -f "$COMPOSE_FILE" up -d fuseki

echo "[2/9] Attesa Fuseki..."
until curl -fsS http://localhost:3030/\$/ping >/dev/null; do
  sleep 2
done
echo "[OK] Fuseki pronto"

echo "[3/9] Generazione dataset sintetico + upload su Fuseki..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 01_Generazione_dati/generate_and_upload_synthetic_to_fuseki.py

echo "[4/9] Calcolo sliding window + entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 03_Sliding_window/sliding_window.py

echo "[5/9] Generazione grafici segnale..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/plot_signal.py

echo "[6/9] Generazione grafici entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/plot_entropy.py

echo "[7/9] Generazione grafici baseline vs entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/plot_baseline_vs_entropy.py

echo "[8/9] Generazione sensitivity analysis..."
for metric in shannon sample permutation; do
  echo "[INFO] Sensitivity metric: $metric"
  docker compose -f "$COMPOSE_FILE" run --rm -e SENSITIVITY_METRIC="$metric" pipeline python 04_Analisi_grafici/plot_sensitivity.py
done

echo "[9/9] Output generati:"
echo
echo "[TABLES]"
find 05_Risultati/tables -maxdepth 2 -type f | sort || true
echo
echo "[FIGURES]"
find 05_Risultati/figures -maxdepth 3 -type f | sort || true

echo
echo "[OK] Pipeline completata"
