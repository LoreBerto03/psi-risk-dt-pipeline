# Supplementary GitHub Material

This directory contains the supplementary material for the thesis repository.
The main thesis includes the figures needed to understand architecture,
methodology, and results at the point where they are discussed. GitHub keeps
the wider reproducibility package and the non-essential experimental outputs.

## Figures

- `figures/final/`: high-resolution curated panels used as final thesis/paper
  figure exports, with captions and notes in `captions_and_notes.md`.
- `figures/entropy/`: additional entropy plots for each scenario and
  window/stride configuration.
- `figures/run_results_summary.txt`: complete text summary of the generated
  figure set.

## Tables And Source Exports

- `tables/final/results_ready_summary.csv`: compact results table for reporting.
- `tables/final/results_ready_summary.tex`: LaTeX version of the compact
  results table.
- `tables/entropy_final.csv`: full sliding-window entropy output used to build
  figures and summaries.
- `tables/raw_points.csv`: raw generated time-series points.
- `tables/synthetic_points_generated.csv`: generated synthetic scenario data.
- `tables/synthetic_points_generated.ttl`: RDF/Turtle export for Fuseki.

## Notes

The pipeline does not currently generate separate full-page screenshots. If
screenshots are added later, they should be stored under `figures/screenshots/`
and listed here.

All files in this directory can be regenerated with:

```bash
bash run_all.sh
```
