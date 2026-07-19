#!/usr/bin/env python3
"""mcp_servers/mdq/index_delete.py

File deletion logic for mdq indexer.

Dependency direction: index_delete → models
Import from here:  from mcp_servers.mdq.index_delete import delete_file_from_index
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mcp_servers.mdq.mdq_service import MdqService


def delete_file_from_index(
    service: MdqService, conn: sqlite3.Connection, path: Path
) -> None:
    """Remove a file's chunks and index_state records from the database."""
    doc_id = hashlib.sha256(str(path).encode()).hexdigest()
    # chunks_ad trigger fires automatically on DELETE — no manual FTS cleanup needed
    conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
    conn.execute("DELETE FROM documents WHERE doc_id = ?", (doc_id,))
    conn.execute(
        "DELETE FROM index_state WHERE key LIKE ?",
        (f"mtime:{str(path)}%",),
    )
    conn.commit()
