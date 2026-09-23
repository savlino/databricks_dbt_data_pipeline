"""Shared Databricks SQL connection helpers."""

from __future__ import annotations

import os
import re

from databricks.sdk import WorkspaceClient


def get_workspace_client() -> WorkspaceClient:
    return WorkspaceClient()


def get_warehouse_id() -> str:
    http_path = os.environ.get("DATABRICKS_HTTP_PATH", "")
    match = re.search(r"/warehouses/([^/]+)$", http_path)
    if not match:
        raise RuntimeError(
            "DATABRICKS_HTTP_PATH must end with /warehouses/<warehouse-id>."
        )
    return match.group(1)


def execute_statement(
    workspace: WorkspaceClient, warehouse_id: str, statement: str
):
    result = workspace.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="50s",
    )
    if not result.status or result.status.state.value != "SUCCEEDED":
        message = (
            result.status.error.message
            if result.status and result.status.error
            else "Databricks SQL statement did not succeed."
        )
        raise RuntimeError(message)
    return result