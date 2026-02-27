#!/bin/bash
set -e

echo "========================================================="
echo "  Avvio Pipeline Riproducibile Ψ-Risk-DT"
echo "========================================================="

echo "[1/4] Creazione alberatura risultati..."
mkdir -p results/figures results/tables

echo "[2/4] Avvio ambiente Docker (Spark + Fuseki)..."
docker compose -f docker/docker-compose.yml up -d
sleep 10 # Attesa tecnica per il boot dei servizi

echo "[3/4] Esecuzione Asse 1: Calcolo Entropia e ∆H..."
python3 scripts/entropy_engine.py

echo "[4/4] Spegnimento pulito dell'ambiente..."
docker compose -f docker/docker-compose.yml down

echo "========================================================="
echo " Pipeline completata! Controlla la cartella /results"
echo "========================================================="