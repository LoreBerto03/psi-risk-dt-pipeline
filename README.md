# PSI-Risk-DT Reproducibility Package

This repository contains a reproducible pipeline for entropy-based drift detection on synthetic PSI-Risk-DT scenarios.

The project generates three synthetic scenarios:
- `A` stable (`stable`)
- `B` gradual drift (`drift_gradual`)
- `C` abrupt shock (`shock`)

and computes Shannon, Sample, and Permutation entropy over sliding windows (`C1..C5`) to produce:
- final curated figures for thesis/Paper 3 (`results/figures/final/`)
- publication-ready summary tables (`results/tables/final/`)
- supplementary GitHub material (`results/`): high-resolution figures, additional plots, source exports, and non-essential experimental outputs

## Prerequisites

Required:
- Docker
- Docker Compose plugin (`docker compose`)

Optional local Python setup (only if you want to run scripts outside containers):
- Python 3.11+

Example `virtualenv` setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Quick Start (End-to-End)

From repository root:

```bash
bash run_all.sh
```

This command runs the full flow:
1. start Fuseki
2. generate synthetic scenarios (fixed seed)
3. upload RDF data to Fuseki
4. compute sliding-window entropy outputs
5. generate entropy plots
6. generate run summary
7. generate final curated figure package
8. generate final results-ready table (`.csv` + `.tex`)

Note: files under `results/` are versioned as supplementary thesis material on GitHub. After a fresh `git clone`, run `bash run_all.sh` to recreate or refresh them locally.

## Core Commands

Full pipeline:

```bash
bash run_all.sh
```

Only final figures:

```bash
docker compose -f docker/docker-compose.yml run --rm --no-deps pipeline python src/analysis/build_final_figure_package.py
```

Only final table:

```bash
docker compose -f docker/docker-compose.yml run --rm --no-deps pipeline python src/analysis/export_results_ready_table.py
```

## Repository Structure

```text
src/
  data_generation/        synthetic dataset generation + Fuseki upload
  entropy/                Shannon / Sample / Permutation entropy implementations
  sliding_window/         sliding-window computation and delta features
  analysis/               plot and export scripts (figures and final tables)
configs/                  central configuration + Docker/Fuseki utilities
results/
  figures/                high-resolution thesis figures and additional entropy plots
  tables/                 source exports and experimental output tables
scripts/                  orchestration scripts (end-to-end run)
docs/                     thesis/paper support documents
docker/                   Dockerfile and docker-compose stack
README.md
run_all.sh                root entrypoint wrapper
```

## Reproducibility Notes

Main reproducibility controls are in [`configs/config.py`](configs/config.py):
- `SYNTHETIC_SEED = 42`
- `SYNTHETIC_POINTS_PER_SCENARIO = 3000`
- drift interval: `DRIFT_START=1000`, `DRIFT_END=2000`
- shock center/width: `SHOCK_CENTER=1500`, `SHOCK_WIDTH=25`
- experiment grid: `C1..C5` (window/stride combinations)

The pipeline is deterministic with fixed seed and centralized configuration.

## GitHub Supplementary Material

The thesis text contains the essential figures where they are discussed. This repository keeps the supplementary material requested for GitHub:
- `results/figures/final/*.png`
- `results/figures/entropy/*.png`
- `results/figures/final/captions_and_notes.md`
- `results/figures/run_results_summary.txt`
- `results/tables/*.csv`
- `results/tables/*.ttl`
- `results/tables/final/results_ready_summary.csv`
- `results/tables/final/results_ready_summary.tex`

See [`results/README.md`](results/README.md) for the full supplementary-material index.
