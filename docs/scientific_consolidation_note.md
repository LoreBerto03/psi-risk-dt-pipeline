## 3.1 Scientific Consolidation of Sensitivity Results

This note consolidates the evidence from the final figure package in `results/figures/final/` and the publication-ready table `results/tables/final/results_ready_summary.csv`. The goal is to provide an interpretive synthesis of the sensitivity analysis rather than a purely descriptive restatement of plots and tabulated values.

### Scenario A: Stable Regime

Under nominal conditions, no detection event is expected; therefore, the relevant criteria are baseline stability, pre-event false positives, and peak `|Delta H|`. By raw false-positive count, the most stable configuration is generally `C5` (`W=128`, `stride=8`), which yields `3` false positives for Shannon, `7` for Sample, and `7` for Permutation. `C4` is the next most stable by the same criterion (`9`, `11`, `10`), whereas `C2` is consistently the least stable in the window-size comparison, especially for Sample (`122` false positives, peak `|Delta H| = 1.280934`).

The interpretation, however, must be qualified. The apparent stability gain of `C4/C5` is partly attributable to coarser temporal sampling, not only to intrinsically smoother entropy behavior. Within the stride-1 comparison (`C2/C1/C3`), the initial design hypothesis is only partially confirmed: reducing `W` does increase baseline instability, but increasing `W` does not uniformly minimize false positives across metrics. For example, `C3` reduces peak amplitude for Shannon (`0.033929` versus `0.060870` in `C1`) and for Permutation (`0.001425` versus `0.004424`), yet it does not outperform `C4/C5` in raw false-positive count.

Methodologically, Scenario A indicates that noise sensitivity is metric- and configuration-dependent. Shannon is generally the noisiest metric in raw counts across `C1`, `C3`, `C4`, and `C5`, while Sample becomes the dominant source of instability in the small-window setting `C2`. This supports using the stable regime as a calibration check, rather than assuming that one metric is globally superior in nominal conditions.

### Scenario B: Gradual Drift

For gradual drift, the earliest overall detection is obtained by Shannon with `C1`, with `t_detect = 1012` and `delay = 12`; see `results/tables/final/results_ready_summary.csv` and `results/figures/final/fig_scenarioB_W_sensitivity_entropy_panel.png`. This observation is important because it directly qualifies the initial expectation that smaller windows should always be more reactive. In the same scenario, `C2` is not the fastest configuration for Shannon (`delay = 36`), although it is faster for Sample (`delay = 27`) and for Permutation (`delay = 47`). Therefore, the statement "smaller windows are more reactive" is not robust in Scenario B; it is metric-specific.

The most stable pre-drift behavior, again by raw false-positive count, is achieved by `C5` for Shannon and Sample (`0` and `4` false positives, respectively), while Permutation attains its minimum in `C3` (`0` false positives). This means that the nominal portion of the gradual-drift run does not yield a single universally best configuration across all metrics. Still, coarser stride settings reduce raw pre-drift activations substantially, at the cost of slower or less precise trend tracking.

Noise sensitivity in Scenario B is dominated by Sample in the small-window setting: `C2` combines relatively fast detection with `32` pre-drift false positives and the highest peak among all entries in the table (`peak |Delta H| = 1.373049`). Shannon is less extreme in peak amplitude but remains sensitive to baseline activity, while Permutation is comparatively conservative in false positives yet often too delayed to be an effective drift monitor outside `C2`.

The methodological implication for PSI-Risk-DT monitoring is that gradual drift should not be monitored with a single heuristic such as "minimize `W`". A more defensible recommendation is to treat Shannon with `C1` or `C3` as the most reliable low-delay solution in this scenario, while recognizing that `C2` improves responsiveness only for selected metrics and at a non-negligible stability cost.

### Scenario C: Shock

For shock, the earliest overall detection is obtained by Permutation with `C1`, with `t_detect = 1451` and `delay = 1`; see `results/tables/final/results_ready_summary.csv` and `results/figures/final/fig_scenarioC_W_sensitivity_entropy_panel.png`. This is the clearest case in which Permutation Entropy provides a specific informational contribution. However, the pattern is not robust across the full configuration grid: the same metric degrades to `delay = 172` in `C3`, and to `10` and `14` in `C4` and `C5`.

Shannon offers a different profile. It is not the earliest in absolute terms, but it is the most consistently fast shock detector across multiple configurations: `delay = 6` in `C2`, `C4`, and `C5`. This makes Shannon more robust than Permutation under configuration changes, even though its raw false-positive counts remain higher (`52`, `22`, and `12`, respectively). Sample is the least competitive metric for shock detection in this setup, with delays between `149` and `210`.

The most stable pre-shock behavior by raw count is obtained by `C5` across all three metrics (`12`, `3`, `8`). Still, this should be interpreted alongside the stride effect visible in `results/figures/final/fig_scenarioC_stride_sensitivity_entropy_panel.png`: part of the apparent stability improvement comes from reduced update density. Thus, the low false-positive count of `C5` does not by itself justify selecting coarse stride as a generally superior choice.

In methodological terms, Scenario C supports a two-level conclusion. First, abrupt events are the regime in which Permutation Entropy is most informative. Second, if robustness across configurations is prioritized over best-case latency, Shannon provides the safer operational choice in the current PSI-Risk-DT setup.

### Cross-Scenario Synthesis

Across scenarios, the initial design hypotheses are only partially confirmed.

- Smaller windows are not uniformly more reactive. This is true for Sample and Permutation in Scenario B, but it is false for Shannon in the same scenario.
- Larger windows often reduce peak amplitude, but they do not guarantee superior nominal stability or an acceptable delay profile. `C3` is notably problematic for shock, especially with Shannon (`delay = 141`, `106` pre-event false positives).
- Larger stride generally smooths the curves and reduces raw false-positive counts, but this comes with lower temporal granularity and does not monotonically improve all metrics. In Scenario C, higher stride improves Shannon delay while worsening Permutation and Sample delay.

The metric-level picture is equally non-uniform. Shannon has the lowest average delay across Scenarios B and C, but also the highest cumulative false-positive burden. Sample is highly sensitive to local fluctuations, especially at `W=64`, and often pays for this sensitivity with elevated baseline activity. Permutation is the most selective metric: weak on gradual drift, but potentially highly informative for sharp shock onset.

### Implications for PSI-Risk-DT Monitoring

The main implication is that PSI-Risk-DT monitoring should be framed as a trade-off problem rather than a single-parameter optimization task. Configuration choice must depend on the anomaly morphology being prioritized.

If gradual drift is the main concern, Shannon with `C1` or `C3` is the most defensible recommendation in the current setup because it combines low delay with a more stable response than the fast-but-noisy alternatives. If abrupt shock detection is the priority, Permutation with `C1` provides the best-case response time, but only as a scenario-specific and configuration-sensitive advantage. If robustness across multiple operating points is preferred, Shannon remains the most reliable primary metric, while Permutation should be retained as a complementary indicator for abrupt-change sensitivity.
