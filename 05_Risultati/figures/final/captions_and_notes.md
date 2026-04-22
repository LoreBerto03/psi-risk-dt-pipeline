# Final Figure Package

This directory contains the curated final figure subset for thesis / Paper 3 integration.
No supplementary figures were added, because the six main panels already cover the non-redundant comparisons on window size and stride across Scenarios A/B/C.

## fig_scenarioA_W_sensitivity_entropy_panel.png

- Figure file: `fig_scenarioA_W_sensitivity_entropy_panel.png`
- Suggested LaTeX label: `fig:fig_scenarioA_W_sensitivity_entropy_panel`
- Caption: Window-size sensitivity for Scenario A (stable). The three rows report Shannon, Sample, and Permutation entropy, respectively, for C2 (W=64, stride=1), C1 (W=128, stride=1), and C3 (W=256, stride=1). Solid lines represent smoothed entropy trajectories, while vertical dotted markers indicate the first threshold crossing estimated from the stable baseline when applicable.
- Interpretive note: The stable case should be read as a baseline smoothness comparison. Smaller windows tend to amplify short-term fluctuations, while larger windows compress local variability and flatten the trajectories.

## fig_scenarioB_W_sensitivity_entropy_panel.png

- Figure file: `fig_scenarioB_W_sensitivity_entropy_panel.png`
- Suggested LaTeX label: `fig:fig_scenarioB_W_sensitivity_entropy_panel`
- Caption: Window-size sensitivity for Scenario B (gradual drift). The three rows report Shannon, Sample, and Permutation entropy, respectively, for C2 (W=64, stride=1), C1 (W=128, stride=1), and C3 (W=256, stride=1). Solid lines represent smoothed entropy trajectories, while vertical dotted markers indicate the first threshold crossing estimated from the stable baseline when applicable.
- Interpretive note: The reader should compare how quickly the three configurations depart from the pre-change regime after t=1000. This panel highlights the reactivity/stability trade-off: shorter windows respond earlier in some metrics, whereas larger windows produce smoother but often delayed transitions.

## fig_scenarioC_W_sensitivity_entropy_panel.png

- Figure file: `fig_scenarioC_W_sensitivity_entropy_panel.png`
- Suggested LaTeX label: `fig:fig_scenarioC_W_sensitivity_entropy_panel`
- Caption: Window-size sensitivity for Scenario C (shock). The three rows report Shannon, Sample, and Permutation entropy, respectively, for C2 (W=64, stride=1), C1 (W=128, stride=1), and C3 (W=256, stride=1). Solid lines represent smoothed entropy trajectories, while vertical dotted markers indicate the first threshold crossing estimated from the stable baseline when applicable.
- Interpretive note: The key point is the response around the shock interval centered at t=1450. The figure shows whether a configuration yields a sharp and early entropy response or a slower, more damped reaction to the abrupt event.

## fig_scenarioA_stride_sensitivity_entropy_panel.png

- Figure file: `fig_scenarioA_stride_sensitivity_entropy_panel.png`
- Suggested LaTeX label: `fig:fig_scenarioA_stride_sensitivity_entropy_panel`
- Caption: Stride sensitivity for Scenario A (stable). The three rows report Shannon, Sample, and Permutation entropy, respectively, for C1 (W=128, stride=1), C4 (W=128, stride=4), and C5 (W=128, stride=8). Solid lines represent smoothed entropy trajectories, while vertical dotted markers indicate the first threshold crossing estimated from the stable baseline when applicable.
- Interpretive note: This panel should be read in terms of curve regularity and temporal granularity. Increasing the stride reduces the density of updates and makes the trajectories visually smoother, but part of this effect comes from coarser sampling rather than intrinsically better stability.

## fig_scenarioB_stride_sensitivity_entropy_panel.png

- Figure file: `fig_scenarioB_stride_sensitivity_entropy_panel.png`
- Suggested LaTeX label: `fig:fig_scenarioB_stride_sensitivity_entropy_panel`
- Caption: Stride sensitivity for Scenario B (gradual drift). The three rows report Shannon, Sample, and Permutation entropy, respectively, for C1 (W=128, stride=1), C4 (W=128, stride=4), and C5 (W=128, stride=8). Solid lines represent smoothed entropy trajectories, while vertical dotted markers indicate the first threshold crossing estimated from the stable baseline when applicable.
- Interpretive note: The important feature is how the onset of change is represented after t=1000. Higher stride values usually make the curves more regular, but they also reduce temporal resolution and can postpone the visible transition associated with drift detection.

## fig_scenarioC_stride_sensitivity_entropy_panel.png

- Figure file: `fig_scenarioC_stride_sensitivity_entropy_panel.png`
- Suggested LaTeX label: `fig:fig_scenarioC_stride_sensitivity_entropy_panel`
- Caption: Stride sensitivity for Scenario C (shock). The three rows report Shannon, Sample, and Permutation entropy, respectively, for C1 (W=128, stride=1), C4 (W=128, stride=4), and C5 (W=128, stride=8). Solid lines represent smoothed entropy trajectories, while vertical dotted markers indicate the first threshold crossing estimated from the stable baseline when applicable.
- Interpretive note: The figure is useful to assess how much temporal downsampling alters the response to an abrupt event. The reader should focus on whether a smoother curve is obtained at the price of later or less precisely localized change indications near the shock interval.
