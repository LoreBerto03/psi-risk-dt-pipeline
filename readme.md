# Ψ-Risk-DT: Reproducible Experimental Pipeline
**Entropy-Based Validation and Ablation Analysis for Neuro-Symbolic Digital Twins**

Questo repository contiene l'implementazione ufficiale del framework **Ψ-Risk-DT**. La pipeline è progettata per essere deterministica e completamente riproducibile, seguendo i criteri di sottomissione **ACM Artifact Evaluation**. Il sistema utilizza **Apache Spark** per l'elaborazione del segnale entropico e **PyTorch** per lo scoring del rischio tramite reti neurali ricorrenti (ARNN).

![Pipeline Architetturale Ψ-Risk-DT]

---

## Quickstart (Riproduzione in 4 step)

Assicurati di avere **Docker** e **Docker Compose** installati.

```bash
# 1. Clona il repository
git clone [https://github.com/tuo-username/psi-risk-dt-pipeline.git](https://github.com/tuo-username/psi-risk-dt-pipeline.git) && cd psi-risk-dt-pipeline

# 2. Avvia l'ambiente (Spark Standalone + Apache Jena Fuseki)
docker-compose -f docker/docker-compose.yml up -d

# 3. Installa le dipendenze Python (venv consigliato)
pip install -r requirements.txt

# 4. Esegui la pipeline completa (Ingestion -> Entropy -> ARNN -> Results)
./run_all.sh

Struttura del Repository

psi-risk-dt-pipeline/
├── data/           # Dataset simulati (SYN Flood, tracce IoT)
├── docker/         # Configurazioni Docker e Docker-compose
├── scripts/        # Core logic (Entropy engine, ARNN model, MSU manager)
├── config/         # Parametri centralizzati (seed, soglie, finestre ∆t)
├── results/        # Output generati automaticamente (Grafici e Tabelle)
└── run_all.sh      # Script unico di esecuzione end-to-end

Output Attesi Dopo l'esecuzione di ./run_all.sh,
verranno generati automaticamente nella cartella results/:results/figures/entropy_drift.png:
Grafico $H(t)$ che mostra la deviazione del segnale durante le finestre di attacco.
results/figures/risk_scoring.png: Output dello score ARNN confrontato con la ground truth.
results/tables/ablation_study.csv: Tabella comparativa delle performance con e senza il gating entropico.

Software Stack
Runtime: Python 3.12.3 (pip 24.0)
Processing: Apache Spark 3.5.8 (PySpark)
ML Framework: PyTorch 2.10.0+cu128
Knowledge Graph: RDFLib 7.5.0 & Apache Jena Fuseki 5.1.0
Storage: PyArrow 23.0.0 (Supporto Parquet ottimizzato)