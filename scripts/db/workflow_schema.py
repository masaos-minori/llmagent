#!/usr/bin/env python3
"""db/workflow_schema.py
DDL for the Metadata DB (workflow.sqlite).

Tables: tasks, attempts, processed_events, artifacts, approvals.
Run as: PYTHONPATH=scripts python -m db.workflow_schema

Canonical DDL source: db/schema_sql.py::build_workflow_schema_sql()
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from db.config import build_db_config
from db.create_schema import _migrate_workflow_schema
from db.schema_sql import build_workflow_schema_sql

logger = logging.getLogger(__name__)


def init_schema() -> None:
    """Create workflow tables using SQLiteHelper for connection-policy consistency.

    Uses the canonical DDL source (build_workflow_schema_sql) instead of
    duplicating DDL here.
    """
    from db.helper import SQLiteHelper

    with SQLiteHelper("workflow").open(write_mode=True) as db:
        if db.conn is None:
            raise RuntimeError("workflow schema: connection not available")
        db.executescript(build_workflow_schema_sql())
        _migrate_workflow_schema(db.conn)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    cfg = build_db_config()
    Path(cfg.workflow_db_path).parent.mkdir(parents=True, exist_ok=True)
    init_schema()
    logger.info("workflow schema initialised: %s", cfg.workflow_db_path)
