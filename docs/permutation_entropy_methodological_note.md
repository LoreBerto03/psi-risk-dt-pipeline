## Permutation Entropy: Methodological Note

### 1. Parameters Tested and Tuning Rationale
Permutation Entropy (PE) was evaluated within the same experimental grid used for the other entropy metrics, in order to preserve comparability across methods. The tested operating conditions were:
- Window/stride configurations: `C1 (W=128, s=1)`, `C2 (W=64, s=1)`, `C3 (W=256, s=1)`, `C4 (W=128, s=4)`, `C5 (W=128, s=8)`.
- Scenarios: `A (stable)`, `B (gradual drift)`, `C (shock)`.
- Detection rule: first threshold crossing on `|Delta H|`, with `tau = mean(stable |Delta H|) + 3 * std(stable |Delta H|)`.

PE internal parameters in the current setup were fixed to:
- `order = 3`
- `delay = 1`
- `normalize = True`

The rationale for this choice was to keep PE numerically stable across all tested windows (including `W=64`), avoid over-parameterization, and ensure direct comparability with Shannon and Sample entropy under an identical detection protocol.

### 2. Tuning Outcome Across Scenarios
Evidence from `results/tables/final/results_ready_summary.csv` shows a scenario-dependent behavior.

For Scenario B (gradual drift), PE is generally delayed in most configurations:
- `C1: delay=369`, `C3: delay=371`, `C4: delay=372`, `C5: delay=376`.
- Only `C2` improves drift responsiveness (`delay=47`), but this behavior is not consistent across the full grid.

For Scenario C (shock), PE can be highly reactive at low stride:
- `C1: delay=1`, `C2: delay=5`.
- Performance degrades for larger window or coarser stride (`C3: 172`, `C4: 10`, `C5: 14`).

For Scenario A (stable), PE exhibits low peak amplitudes compared with Sample entropy and often with Shannon (e.g., `C1 peak |Delta H| = 0.004424`), but this does not systematically translate into the lowest pre-event false-positive count in all configurations.

### 3. Interpretation of the Observed Behavior
In this pipeline, PE appears selectively sensitive to abrupt ordinal changes (shock-like events), especially when temporal resolution is high (`s=1`). Conversely, for gradual drift, PE often responds late, suggesting lower sensitivity to smooth distributional transitions in the tested operating regime.

This pattern is consistent with the observed combination of:
- very small PE peak scale in several settings, and
- strong dependence on configuration when event morphology changes from abrupt to gradual.

Therefore, PE contributes useful information in specific shock-oriented operating points, but it is less robust as a general-purpose detector across both drift and shock scenarios.

### 4. Final Decision on the Role of PE in This Work
The metric is retained in the study as a secondary, complementary indicator rather than a primary detection metric.

Methodological conclusion:
- PE provides a clear added value for fast shock onset detection in selected low-stride configurations.
- PE is less informative for gradual-drift monitoring under the current setup, due to recurrent large delays in most configurations.

Accordingly, final monitoring recommendations prioritize Shannon/Sample for broad operating coverage, while PE is reported as a targeted metric for abrupt-change sensitivity analysis.
