import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"

for p in [PROJECT_ROOT, CONFIG_DIR]:
    if str(p) not in sys.path:
        sys.path.append(str(p))

from config import (
    DRIFT_END,
    DRIFT_START,
    ENTROPY_METRICS,
    ENTROPY_RESULT_FILE,
    FIGURES_DIR,
    SHOCK_CENTER,
    SHOCK_WIDTH,
    ensure_directories,
)

PLOT_SMOOTH_POINTS = int(os.getenv("PLOT_SMOOTH_POINTS", "25"))
THRESHOLD_STD_FACTOR = float(os.getenv("SENSITIVITY_STD_FACTOR", "3.0"))
FINAL_DIR = FIGURES_DIR / "final"
CAPTIONS_FILE = FINAL_DIR / "captions_and_notes.md"

SCENARIO_META = {
    "stable": {
        "letter": "A",
        "title": "Stable",
        "paper_name": "Scenario A (stable)",
        "short_name": "scenarioA",
    },
    "drift_gradual": {
        "letter": "B",
        "title": "Gradual Drift",
        "paper_name": "Scenario B (gradual drift)",
        "short_name": "scenarioB",
    },
    "shock": {
        "letter": "C",
        "title": "Shock",
        "paper_name": "Scenario C (shock)",
        "short_name": "scenarioC",
    },
}

METRIC_META = {
    "shannon": {
        "pretty": "Shannon",
        "entropy_col": "entropy_shannon",
        "delta_col": "delta_h_shannon_abs",
        "color": "#1d4ed8",
    },
    "sample": {
        "pretty": "Sample",
        "entropy_col": "entropy_sample",
        "delta_col": "delta_h_sample_abs",
        "color": "#16a34a",
    },
    "permutation": {
        "pretty": "Permutation",
        "entropy_col": "entropy_permutation",
        "delta_col": "delta_h_permutation_abs",
        "color": "#7c3aed",
    },
}

COMPARISON_META = {
    "W": {
        "title": "Window-Size Sensitivity",
        "slug": "W_sensitivity",
        "configs": [
            ("C2", 64, 1, "#d97706"),
            ("C1", 128, 1, "#2563eb"),
            ("C3", 256, 1, "#059669"),
        ],
        "caption_suffix": "The three rows report Shannon, Sample, and Permutation entropy, respectively, for C2 (W=64, stride=1), C1 (W=128, stride=1), and C3 (W=256, stride=1).",
        "note_template": {
            "stable": (
                "The stable case should be read as a baseline smoothness comparison. "
                "Smaller windows tend to amplify short-term fluctuations, while larger windows compress local variability and flatten the trajectories."
            ),
            "drift_gradual": (
                "The reader should compare how quickly the three configurations depart from the pre-change regime after t=1000. "
                "This panel highlights the reactivity/stability trade-off: shorter windows respond earlier in some metrics, whereas larger windows produce smoother but often delayed transitions."
            ),
            "shock": (
                "The key point is the response around the shock interval centered at t=1450. "
                "The figure shows whether a configuration yields a sharp and early entropy response or a slower, more damped reaction to the abrupt event."
            ),
        },
    },
    "stride": {
        "title": "Stride Sensitivity",
        "slug": "stride_sensitivity",
        "configs": [
            ("C1", 128, 1, "#2563eb"),
            ("C4", 128, 4, "#d97706"),
            ("C5", 128, 8, "#059669"),
        ],
        "caption_suffix": "The three rows report Shannon, Sample, and Permutation entropy, respectively, for C1 (W=128, stride=1), C4 (W=128, stride=4), and C5 (W=128, stride=8).",
        "note_template": {
            "stable": (
                "This panel should be read in terms of curve regularity and temporal granularity. "
                "Increasing the stride reduces the density of updates and makes the trajectories visually smoother, but part of this effect comes from coarser sampling rather than intrinsically better stability."
            ),
            "drift_gradual": (
                "The important feature is how the onset of change is represented after t=1000. "
                "Higher stride values usually make the curves more regular, but they also reduce temporal resolution and can postpone the visible transition associated with drift detection."
            ),
            "shock": (
                "The figure is useful to assess how much temporal downsampling alters the response to an abrupt event. "
                "The reader should focus on whether a smoother curve is obtained at the price of later or less precisely localized change indications near the shock interval."
            ),
        },
    },
}


def find_input_file() -> Path:
    candidates = [
        ENTROPY_RESULT_FILE,
        PROJECT_ROOT / "results" / "tables" / "entropy_final.csv",
        PROJECT_ROOT / "results" / "tables" / "entropy_over_time.csv",
    ]

    for path in candidates:
        if path.exists():
            return path

    searched = "\n".join(str(p) for p in candidates)
    raise FileNotFoundError(
        "Nessun file risultati trovato.\n"
        f"Percorsi controllati:\n{searched}"
    )


def smooth_series(series: pd.Series, points: int) -> pd.Series:
    if points <= 1:
        return series.copy()
    return series.rolling(points, center=True, min_periods=1).mean()


def event_start_for_scenario(scenario: str) -> float | None:
    if scenario == "drift_gradual":
        return float(DRIFT_START)
    if scenario == "shock":
        return float(SHOCK_CENTER - (2 * SHOCK_WIDTH))
    return None


def add_scenario_highlight(ax, scenario: str) -> None:
    if scenario == "drift_gradual":
        ax.axvspan(
            DRIFT_START,
            DRIFT_END,
            color="#f59e0b",
            alpha=0.14,
        )
    elif scenario == "shock":
        half_width = SHOCK_WIDTH * 2
        ax.axvspan(
            SHOCK_CENTER - half_width,
            SHOCK_CENTER + half_width,
            color="#ef4444",
            alpha=0.14,
        )


def compute_tau_from_stable(stable_df: pd.DataFrame, delta_col: str) -> float:
    values = stable_df[delta_col].fillna(0.0).to_numpy(dtype=float)
    return float(values.mean() + THRESHOLD_STD_FACTOR * values.std(ddof=0))


def compute_detection_time(
    scenario_df: pd.DataFrame,
    stable_df: pd.DataFrame,
    scenario: str,
    delta_col: str,
    time_column: str = "t_center",
) -> float:
    event_start = event_start_for_scenario(scenario)
    if event_start is None:
        return float("nan")

    tau = compute_tau_from_stable(stable_df, delta_col)
    signal = scenario_df[delta_col].fillna(0.0).to_numpy(dtype=float)
    times = scenario_df[time_column].to_numpy(dtype=float)

    post_mask = times >= event_start
    post_times = times[post_mask]
    post_signal = signal[post_mask]
    detections = post_times[post_signal > tau]

    if detections.size == 0:
        return float("nan")

    return float(detections[0])


def compute_plot_limits(series_list: list[pd.Series]) -> tuple[float, float]:
    combined = pd.concat(series_list, ignore_index=True).dropna()
    if combined.empty:
        return (0.0, 1.0)

    vmin = float(combined.min())
    vmax = float(combined.max())
    if np.isclose(vmin, vmax):
        vmax = vmin + 1e-3

    padding = max(0.05 * (vmax - vmin), 1e-3)
    return (max(0.0, vmin - padding), vmax + padding)


def build_caption(scenario: str, comparison_key: str) -> str:
    scenario_meta = SCENARIO_META[scenario]
    comparison_meta = COMPARISON_META[comparison_key]
    factor_name = (
        "window-size"
        if comparison_key == "W"
        else "stride"
    )

    return (
        f"{factor_name.capitalize()} sensitivity for {scenario_meta['paper_name']}. "
        f"{comparison_meta['caption_suffix']} "
        "Solid lines represent smoothed entropy trajectories, while vertical dotted markers "
        "indicate the first threshold crossing estimated from the stable baseline when applicable."
    )


def build_note(scenario: str, comparison_key: str) -> str:
    return COMPARISON_META[comparison_key]["note_template"][scenario]


def generate_comparison_figure(
    df: pd.DataFrame,
    scenario: str,
    comparison_key: str,
) -> tuple[Path, str, str]:
    scenario_meta = SCENARIO_META[scenario]
    comparison_meta = COMPARISON_META[comparison_key]
    configs = comparison_meta["configs"]

    fig, axes = plt.subplots(
        nrows=3,
        ncols=1,
        figsize=(13, 11),
        sharex=True,
    )

    legend_handles = None
    legend_labels = None

    for ax, metric in zip(axes, ENTROPY_METRICS):
        metric_meta = METRIC_META[metric]
        entropy_col = metric_meta["entropy_col"]
        delta_col = metric_meta["delta_col"]

        series_list = []
        for config_id, window_size, stride, color in configs:
            config_df = (
                df[
                    (df["configuration"] == config_id) &
                    (df["scenario"] == scenario) &
                    (df["window_size"] == window_size) &
                    (df["stride"] == stride)
                ]
                .copy()
                .sort_values("t_center")
            )
            if config_df.empty:
                continue

            smoothed = smooth_series(config_df[entropy_col], PLOT_SMOOTH_POINTS)
            series_list.append(smoothed)

            label_suffix = (
                f"W={window_size}, s={stride}"
                if comparison_key == "W"
                else f"s={stride}"
            )
            ax.plot(
                config_df["t_center"],
                smoothed,
                color=color,
                linewidth=2.2,
                label=f"{config_id} ({label_suffix})",
            )

            if scenario != "stable":
                stable_df = (
                    df[
                        (df["configuration"] == config_id) &
                        (df["scenario"] == "stable") &
                        (df["window_size"] == window_size) &
                        (df["stride"] == stride)
                    ]
                    .copy()
                    .sort_values("t_center")
                )
                detection_time = compute_detection_time(
                    scenario_df=config_df,
                    stable_df=stable_df,
                    scenario=scenario,
                    delta_col=delta_col,
                )
                if np.isfinite(detection_time):
                    ax.axvline(
                        detection_time,
                        color=color,
                        linestyle=":",
                        linewidth=1.4,
                        alpha=0.9,
                    )

        y_min, y_max = compute_plot_limits(series_list)
        add_scenario_highlight(ax, scenario)
        ax.set_ylim(y_min, y_max)
        ax.set_ylabel(f"{metric_meta['pretty']} H(t)")
        ax.grid(True, alpha=0.25)

        if legend_handles is None:
            legend_handles, legend_labels = ax.get_legend_handles_labels()

    axes[-1].set_xlabel("time")

    fig.suptitle(
        f"{scenario_meta['paper_name']} - {comparison_meta['title']}",
        fontsize=15,
        y=0.985,
    )
    if legend_handles:
        fig.legend(
            legend_handles,
            legend_labels,
            loc="upper center",
            ncol=len(legend_labels),
            frameon=False,
            bbox_to_anchor=(0.5, 0.955),
        )

    fig.tight_layout(rect=(0.02, 0.03, 0.98, 0.92))

    output_file = FINAL_DIR / (
        f"fig_{scenario_meta['short_name']}_{comparison_meta['slug']}_entropy_panel.png"
    )
    fig.savefig(output_file, dpi=200)
    plt.close(fig)

    return output_file, build_caption(scenario, comparison_key), build_note(scenario, comparison_key)


def write_captions_file(entries: list[dict]) -> bool:
    if CAPTIONS_FILE.exists():
        print(f"[INFO] Captions file already present, keeping existing file: {CAPTIONS_FILE}")
        return False

    lines = [
        "# Final Figure Package",
        "",
        "This directory contains the curated final figure subset for thesis / Paper 3 integration.",
        "No supplementary figures were added, because the six main panels already cover the non-redundant comparisons on window size and stride across Scenarios A/B/C.",
        "",
    ]

    for entry in entries:
        lines.extend(
            [
                f"## {entry['file'].name}",
                "",
                f"- Figure file: `{entry['file'].name}`",
                f"- Suggested LaTeX label: `fig:{entry['file'].stem}`",
                f"- Caption: {entry['caption']}",
                f"- Interpretive note: {entry['note']}",
                "",
            ]
        )

    CAPTIONS_FILE.write_text("\n".join(lines), encoding="utf-8")
    return True


def main() -> None:
    ensure_directories()
    FINAL_DIR.mkdir(parents=True, exist_ok=True)

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    required_columns = {
        "configuration",
        "scenario",
        "window_size",
        "stride",
        "t_center",
        "entropy_shannon",
        "entropy_sample",
        "entropy_permutation",
        "delta_h_shannon_abs",
        "delta_h_sample_abs",
        "delta_h_permutation_abs",
    }
    missing = required_columns - set(df.columns)
    if missing:
        raise RuntimeError(
            f"Il file risultati non contiene le colonne richieste: {sorted(missing)}"
        )

    entries = []
    for comparison_key in ["W", "stride"]:
        for scenario in ["stable", "drift_gradual", "shock"]:
            output_file, caption, note = generate_comparison_figure(
                df=df,
                scenario=scenario,
                comparison_key=comparison_key,
            )
            entries.append(
                {
                    "file": output_file,
                    "caption": caption,
                    "note": note,
                }
            )
            print(f"[OK] Saved final figure: {output_file}")

    captions_created = write_captions_file(entries)
    if captions_created:
        print(f"[OK] Saved captions file: {CAPTIONS_FILE}")


if __name__ == "__main__":
    main()
