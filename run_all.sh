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

echo "[1/5] Avvio servizi Docker..."
docker compose -f "$COMPOSE_FILE" up -d spark spark-worker fuseki

echo "[2/5] Attesa Fuseki..."
until curl -s http://localhost:3030/\$/ping >/dev/null; do
  sleep 2
done
echo "[OK] Fuseki pronto"

echo "[3/5] Calcolo entropia + sliding window..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 03_Sliding_window/sliding_window.py

echo "[4/5] Generazione grafici..."
docker compose -f "$COMPOSE_FILE" run --rm pipeline python 04_Analisi_grafici/plot_entropy.py

echo "[5/5] Output generati:"
ls -lah 05_Risultati/figures || true

echo "[OK] Pipeline completata"