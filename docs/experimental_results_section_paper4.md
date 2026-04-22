## 3.2 Experimental Results

### 3.2.1 Experimental Setup Recap
The experimental campaign evaluates entropy-based monitoring on three synthetic scenarios: `A (stable)`, `B (gradual drift)`, and `C (shock)`. The time axis contains 3000 points per scenario. In Scenario B, drift is active in `t=1000..2000`; in Scenario C, the shock event starts at `t=1450`.

Five sliding-window configurations are tested:
- `C1`: `W=128`, `stride=1` (reference)
- `C2`: `W=64`, `stride=1` (smaller window)
- `C3`: `W=256`, `stride=1` (larger window)
- `C4`: `W=128`, `stride=4` (medium stride)
- `C5`: `W=128`, `stride=8` (coarse stride)

Three entropy metrics are compared: Shannon, Sample, and Permutation. Detection is based on `|Delta H|` with threshold `tau = mean(stable |Delta H|) + 3 * std(stable |Delta H|)`. Reported quantities are detection time (`t_detect`), detection delay, pre-event false positives, and peak `|Delta H|`.

All numeric values cited below come from `results/tables/final/results_ready_summary.csv` (and the equivalent LaTeX table `results/tables/final/results_ready_summary.tex`). Visual behavior is referenced to the curated figure package in `results/figures/final/`.

### 3.2.2 Sensitivity to Window Size
Window-size sensitivity is assessed by comparing `C2/C1/C3` at fixed `stride=1`; see:
- `results/figures/final/fig_scenarioA_W_sensitivity_entropy_panel.png`
- `results/figures/final/fig_scenarioB_W_sensitivity_entropy_panel.png`
- `results/figures/final/fig_scenarioC_W_sensitivity_entropy_panel.png`

For Scenario B (gradual drift), behavior depends on the metric. Shannon does not show monotonic acceleration with smaller windows: delay is `36` in `C2`, `12` in `C1`, and `14` in `C3`. Sample is fastest in `C2` (`delay=27`) but with higher pre-event false positives (`32`) than `C3` (`17`). Permutation benefits strongly from `C2` (`delay=47`) while `C1` and `C3` remain late (`369` and `371`).

For Scenario C (shock), the same factor yields mixed effects. Shannon improves from `delay=50` (`C1`) to `6` (`C2`), but `C3` is substantially slower (`141`) and has the highest pre-event false positives (`106`). Sample remains slow across all three windows (`149`, `152`, `210`). Permutation is fastest in `C1` (`delay=1`), still fast in `C2` (`5`), and slower in `C3` (`172`).

In Scenario A (stable), smaller windows generally increase baseline activity for some metrics: for Sample, pre-event false positives increase from `44` (`C1`) to `122` (`C2`), and peak `|Delta H|` rises from `0.481177` to `1.280934`. Conversely, larger windows may damp peaks (e.g., Shannon peak `0.033929` in `C3` vs `0.060870` in `C1`) but can coincide with slower reaction in event scenarios.

### 3.2.3 Sensitivity to Stride
Stride sensitivity is assessed by comparing `C1/C4/C5` at fixed `W=128`; see:
- `results/figures/final/fig_scenarioA_stride_sensitivity_entropy_panel.png`
- `results/figures/final/fig_scenarioB_stride_sensitivity_entropy_panel.png`
- `results/figures/final/fig_scenarioC_stride_sensitivity_entropy_panel.png`

In Scenario B (gradual drift), increasing stride generally increases delay: Shannon moves from `12` (`C1`) to `120` (`C4`) and `80` (`C5`); Sample from `75` to `80` (`C4` and `C5`); Permutation from `369` to `372` and `376`. This indicates reduced temporal responsiveness as updates become sparser.

In Scenario C (shock), the effect is metric-dependent. Shannon improves (`50` in `C1` to `6` in both `C4` and `C5`), while Sample degrades (`152` to `154` and `158`) and Permutation degrades (`1` to `10` and `14`). Therefore, stride cannot be interpreted as a uniformly beneficial parameter.

For Scenario A, absolute false positives decrease for Shannon (`65` in `C1`, `9` in `C4`, `3` in `C5`), but this should be interpreted as an empirical count trend, not as universal evidence of better operating characteristics across all metrics and scenarios.

### 3.2.4 Cross-Metric Comparison
Across Scenarios B and C (all configurations), Shannon provides the lowest average delay (`47.1`), Sample is intermediate (`111.5`), and Permutation is highest (`173.7`). These averages are directly computed from the corresponding rows in `results_ready_summary.csv`.

At the same time, Shannon accumulates the highest total pre-event false positives (`346`), compared with Sample (`187`) and Permutation (`155`). Peak intensity also differs substantially: Sample frequently exhibits the largest peak `|Delta H|` values (up to `1.373049` in Scenario B, `C2`), while Permutation remains on a lower scale (typically around `10^-3` to `10^-2` in many configurations).

The cross-metric evidence therefore supports a non-dominance conclusion: lower delay does not systematically coincide with lower false positives or lower peak excursions.

### 3.2.5 Key Takeaway for PSI-Risk-DT Monitoring
The final evidence supports a practical trade-off interpretation for PSI-Risk-DT monitoring.

First, no single configuration-metric pair is uniformly best across stable, drift, and shock regimes. Second, parameter effects are scenario- and metric-dependent: reducing `W` can improve reactivity in selected cases but may also amplify baseline activity; increasing stride can reduce temporal detail and can either help or hurt delay, depending on the metric.

From an operational perspective, the recommended practice is to select configuration-metric pairs according to the target anomaly profile and tolerance to false positives, using the final figures (`results/figures/final/*.png`) for qualitative behavior inspection and the final table (`results/tables/final/results_ready_summary.csv`) for quantitative verification.
