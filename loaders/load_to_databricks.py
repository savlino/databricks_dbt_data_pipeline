"""Upload the source CSV files to a Unity Catalog volume and rebuild raw Delta tables."""

from __future__ import annotations

import argparse
from pathlib import Path

from databricks_sql import execute_statement, get_workspace_client


DEFAULT_SOURCE_DIR = Path(
    r"C:\Users\A200072285\Documents\wrkk\airflow_climbers_data\airflow\data"
)
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
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
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
    ensure_sources_exist(args.source_dir)

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
        local_path = args.source_dir / filename
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