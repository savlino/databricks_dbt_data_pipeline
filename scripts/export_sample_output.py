"""Export the analytics mart to CSV and render a sample chart."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

import matplotlib
import pandas as pd


matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "loaders"))

from databricks_sql import execute_statement, get_warehouse_id, get_workspace_client


OUTPUT_DIR = PROJECT_ROOT / "sample_output"
CSV_PATH = OUTPUT_DIR / "climber_country_sex_stats.csv"
CHART_PATH = OUTPUT_DIR / "top_countries_by_climbers.png"
NUMERIC_COLUMNS = [
    "climber_count",
    "avg_age",
    "avg_grade_numeric",
    "median_height",
    "max_grade_numeric",
    "max_grade_climber_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, help="Maximum number of rows to export")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than zero")
    return args


def safe_identifier(value: str, variable_name: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise RuntimeError(f"{variable_name} is not a valid SQL identifier.")
    return value


def export(limit: int | None) -> None:
    catalog = safe_identifier(
        os.environ.get("DATABRICKS_CATALOG", ""), "DATABRICKS_CATALOG"
    )
    schema = safe_identifier(
        os.environ.get("DATABRICKS_SCHEMA", ""), "DATABRICKS_SCHEMA"
    )
    limit_clause = f" LIMIT {limit}" if limit is not None else ""
    statement = (
        f"SELECT * FROM `{catalog}`.`{schema}`.`climber_country_sex_stats` "
        f"ORDER BY climber_count DESC{limit_clause}"
    )

    print("Querying climber_country_sex_stats from Databricks...")
    result = execute_statement(
        get_workspace_client(), get_warehouse_id(), statement
    )
    columns = [column.name for column in result.manifest.schema.columns]
    rows = result.result.data_array if result.result else []
    frame = pd.DataFrame(rows, columns=columns)
    for column in NUMERIC_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(CSV_PATH, index=False)
    print(f"Exported {len(frame)} rows to {CSV_PATH}.")

    top_countries = (
        frame.groupby("country")["climber_count"]
        .sum()
        .nlargest(10)
        .index
    )
    chart_data = (
        frame[frame["country"].isin(top_countries)]
        .pivot_table(
            index="country",
            columns="sex",
            values="climber_count",
            aggfunc="sum",
            fill_value=0,
        )
        .reindex(top_countries[::-1])
        .reindex(columns=["F", "M"], fill_value=0)
    )
    figure, axis = plt.subplots(figsize=(10, 6))
    chart_data.plot.barh(ax=axis, color=["#d95f76", "#2878b5"], width=0.8)
    axis.set_xlabel("Climbers")
    axis.set_ylabel("Country")
    axis.set_title("Top countries by climber count and sex")
    axis.legend(title="Sex")
    figure.tight_layout()
    figure.savefig(CHART_PATH, dpi=160)
    plt.close(figure)
    print(f"Saved chart to {CHART_PATH}.")


def main() -> int:
    args = parse_args()
    try:
        export(args.limit)
    except Exception as error:
        print(f"Export failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())