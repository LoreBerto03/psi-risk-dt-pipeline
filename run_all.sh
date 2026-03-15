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

trap cleanup EXIT

echo "[1/7] Avvio servizi Docker..."
docker compose -f "$COMPOSE_FILE" up -d spark spark-worker fuseki

echo "[2/7] Attesa Fuseki..."
until curl -fsS http://localhost:3030/\$/ping >/dev/null; do
  sleep 2
done
echo "[OK] Fuseki pronto"

echo "[3/7] Calcolo sliding window + entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 03_Sliding_window/sliding_window.py

echo "[4/7] Generazione grafici segnale..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/plot_signal.py

echo "[5/7] Generazione grafici entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/plot_entropy.py

echo "[6/7] Generazione grafici baseline vs entropia..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/plot_baseline_vs_entropy.py

echo "[7/7] Output generati:"
echo
echo "[TABLES]"
ls -lah 05_Risultati/tables || true
echo
echo "[FIGURES]"
ls -lah 05_Risultati/figures || true

echo "[OK] Pipeline completata"