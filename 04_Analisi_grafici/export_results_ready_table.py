import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = PROJECT_ROOT / "04_Analisi_grafici"
CONFIG_DIR = PROJECT_ROOT / "Config"

for p in [PROJECT_ROOT, ANALYSIS_DIR, CONFIG_DIR]:
    if str(p) not in sys.path:
        sys.path.append(str(p))

from config import EXPERIMENT_CONFIGS, TABLES_DIR, ensure_directories
from export_run_results import (
    METRIC_ORDER,
    SCENARIO_ORDER,
    build_summary,
    find_input_file,
    format_time,
)

OUTPUT_DIR = TABLES_DIR / "final"
CSV_OUTPUT_FILE = OUTPUT_DIR / "results_ready_summary.csv"
TEX_OUTPUT_FILE = OUTPUT_DIR / "results_ready_summary.tex"

SCENARIO_PUBLICATION_LABEL = {
    "stable": "A (stable)",
    "drift_gradual": "B (gradual drift)",
    "shock": "C (shock)",
}

METRIC_LATEX_LABEL = {
    "Shannon": "Shannon",
    "Sample": "Sample",
    "Permutation": "Permutation",
}


def format_peak(value: float) -> str:
    return f"{float(value):.6f}"


def format_latex_time(value) -> str:
    formatted = format_time(value)
    return "--" if formatted == "N/A" else formatted


def build_results_ready_table(summary_df: pd.DataFrame) -> pd.DataFrame:
    config_order = {config["id"]: idx for idx, config in enumerate(EXPERIMENT_CONFIGS)}

    display_df = summary_df[
        [
            "configuration",
            "window_size",
            "stride",
            "metric",
            "detection_time",
            "delay",
            "false_positives",
            "peak_intensity",
        ]
    ].copy()

    display_df["scenario_label"] = summary_df["scenario"].map(SCENARIO_PUBLICATION_LABEL)
    display_df["config_order"] = display_df["configuration"].map(config_order)
    display_df["scenario_order"] = summary_df["scenario"].map(SCENARIO_ORDER)
    display_df["metric_order"] = display_df["metric"].str.lower().map(METRIC_ORDER)

    display_df = display_df.sort_values(
        ["scenario_order", "config_order", "metric_order"]
    ).reset_index(drop=True)

    display_df["t_detect"] = display_df["detection_time"].map(format_time)
    display_df["detection_delay"] = display_df["delay"].map(format_time)
    display_df["pre_event_false_positives"] = display_df["false_positives"].astype(int)
    display_df["peak_abs_delta_h"] = display_df["peak_intensity"].map(format_peak)

    return display_df.rename(
        columns={
            "scenario_label": "scenario",
            "configuration": "configuration_id",
            "window_size": "W",
            "metric": "entropy_metric",
        }
    )[
        [
            "scenario",
            "configuration_id",
            "W",
            "stride",
            "entropy_metric",
            "t_detect",
            "detection_delay",
            "pre_event_false_positives",
            "peak_abs_delta_h",
        ]
    ]


def write_csv(display_df: pd.DataFrame) -> None:
    display_df.to_csv(CSV_OUTPUT_FILE, index=False, encoding="utf-8")
    print(f"[OK] Saved CSV table: {CSV_OUTPUT_FILE}")


def write_latex(display_df: pd.DataFrame) -> None:
    latex_df = display_df.copy()
    latex_df["entropy_metric"] = latex_df["entropy_metric"].map(METRIC_LATEX_LABEL)
    latex_df["t_detect"] = latex_df["t_detect"].replace({"N/A": "--"})
    latex_df["detection_delay"] = latex_df["detection_delay"].replace({"N/A": "--"})

    header = [
        "\\begin{longtable}{llrrlrrrl}",
        "\\caption{Results-ready summary of the entropy-based sensitivity analysis across scenarios, configurations, and metrics. For Scenario A (stable), $t_{detect}$ and detection delay are not applicable; the false-positive count is computed over the full stable run.}\\label{tab:results-ready-summary}\\\\",
        "\\toprule",
        "Scenario & Config. & $W$ & Stride & Metric & $t_{detect}$ & Delay & Pre-event FP & Peak $|\\Delta H|$ \\\\",
        "\\midrule",
        "\\endfirsthead",
        "\\multicolumn{9}{l}{\\tablename\\ \\thetable{} -- continued from previous page}\\\\",
        "\\toprule",
        "Scenario & Config. & $W$ & Stride & Metric & $t_{detect}$ & Delay & Pre-event FP & Peak $|\\Delta H|$ \\\\",
        "\\midrule",
        "\\endhead",
        "\\midrule",
        "\\multicolumn{9}{r}{Continued on next page}\\\\",
        "\\endfoot",
        "\\bottomrule",
        "\\endlastfoot",
    ]

    body = []
    for row in latex_df.itertuples(index=False):
        body.append(
            " & ".join(
                [
                    str(row.scenario),
                    str(row.configuration_id),
                    str(row.W),
                    str(row.stride),
                    str(row.entropy_metric),
                    str(row.t_detect),
                    str(row.detection_delay),
                    str(row.pre_event_false_positives),
                    str(row.peak_abs_delta_h),
                ]
            )
            + " \\\\"
        )

    footer = ["\\end{longtable}", ""]
    TEX_OUTPUT_FILE.write_text("\n".join(header + body + footer), encoding="utf-8")
    print(f"[OK] Saved LaTeX table: {TEX_OUTPUT_FILE}")


def main() -> None:
    ensure_directories()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    input_file = find_input_file()
    df = pd.read_csv(input_file)

    summary_df = build_summary(df, time_column="t_center")
    if summary_df.empty:
        raise RuntimeError("No results available to build the publication-ready table.")

    display_df = build_results_ready_table(summary_df)
    write_csv(display_df)
    write_latex(display_df)


if __name__ == "__main__":
    main()
