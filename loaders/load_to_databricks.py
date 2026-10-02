"""Download the Kaggle dataset, upload it to a Unity Catalog volume, and rebuild raw Delta tables."""

from __future__ import annotations


import kagglehub
import argparse
from pathlib import Path

from databricks_sql import execute_statement, get_workspace_client


KAGGLE_DATASET = "jordizar/climb-dataset"
DEFAULT_CATALOG = "main"
DEFAULT_VOLUME_SCHEMA = "climbers"
DEFAULT_VOLUME = "raw_volume"
DEFAULT_RAW_SCHEMA = "raw"

FILES = {
    "climber_df.csv": "climbers",
    "grades_conversion_table.csv": "grades",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        help="Use an existing local dataset directory instead of downloading from Kaggle",
    )
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--volume-schema", default=DEFAULT_VOLUME_SCHEMA)
    parser.add_argument("--volume", default=DEFAULT_VOLUME)
    parser.add_argument("--raw-schema", default=DEFAULT_RAW_SCHEMA)
    parser.add_argument("--warehouse-id", required=True)
    return parser.parse_args()


def ensure_sources_exist(source_dir: Path) -> None:
    missing_files = [name for name in FILES if not (source_dir / name).is_file()]
    if missing_files:
        missing = ", ".join(missing_files)
        raise FileNotFoundError(f"Missing source CSV file(s) in {source_dir}: {missing}")


def main() -> None:
    args = parse_args()
    source_dir = args.source_dir
    if source_dir is None:
        print(f"Downloading latest Kaggle dataset: {KAGGLE_DATASET}...")
        source_dir = Path(kagglehub.dataset_download(KAGGLE_DATASET))
        print(f"Dataset downloaded to {source_dir}.")
    ensure_sources_exist(source_dir)

    workspace = get_workspace_client()
    volume_fqn = f"{args.catalog}.{args.volume_schema}.{args.volume}"
    volume_path = f"/Volumes/{args.catalog}/{args.volume_schema}/{args.volume}"

    execute_statement(
        workspace,
        args.warehouse_id,
        f"CREATE VOLUME IF NOT EXISTS {volume_fqn}",
    )
    execute_statement(
        workspace,
        args.warehouse_id,
        f"CREATE SCHEMA IF NOT EXISTS {args.catalog}.{args.raw_schema}",
    )

    for filename, table_name in FILES.items():
        local_path = source_dir / filename
        volume_file_path = f"{volume_path}/{filename}"
        with local_path.open("rb") as source_file:
            workspace.files.upload(volume_file_path, source_file, overwrite=True)

        execute_statement(
            workspace,
            args.warehouse_id,
            (
                f"CREATE OR REPLACE TABLE {args.catalog}.{args.raw_schema}.{table_name} "
                f"USING DELTA AS SELECT * FROM read_files("
                f"'{volume_file_path}', format => 'csv', header => true, "
                f"inferColumnTypes => true)"
            ),
        )


if __name__ == "__main__":
    main()