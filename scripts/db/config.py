#!/usr/bin/env python3
"""db/config.py
DbConfig dataclass and builder for SQLite database paths.

Separated from agent/config.py so that db/ layer modules can reference
database configuration without importing from agent/.
embed_url belongs to the embedding service layer (agent/config.py), not here.
sqlite_vec_so is optional; empty string means vec extension is not required.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shared.config_loader import ConfigLoader


@dataclass(frozen=True)
class DbConfig:
    """Immutable configuration for the SQLite database."""

    rag_db_path: str
    session_db_path: str
    workflow_db_path: str = "/opt/llm/db/workflow.sqlite"
    eventbus_db_path: str = "/opt/llm/db/eventbus.sqlite"
    sqlite_vec_so: str = ""  # empty = vec extension not required
    sqlite_timeout: int = 30
    sqlite_busy_timeout_ms: int = 30000
    embedding_dims: int = 384

    def __post_init__(self) -> None:
        if not self.rag_db_path:
            raise ValueError("rag_db_path must not be empty")
        if not self.session_db_path:
            raise ValueError("session_db_path must not be empty")
        if not self.workflow_db_path:
            raise ValueError("workflow_db_path must not be empty")
        if not self.eventbus_db_path:
            raise ValueError("eventbus_db_path must not be empty")
        if self.sqlite_timeout < 1:
            raise ValueError(f"sqlite_timeout must be >= 1, got {self.sqlite_timeout}")
        if self.embedding_dims < 1:
            raise ValueError(f"embedding_dims must be >= 1, got {self.embedding_dims}")
        # DB files are created automatically by SQLite on first open;
        # validate that the parent directory exists rather than the file itself.
        for label, path_str in (
            ("rag_db_path", self.rag_db_path),
            ("session_db_path", self.session_db_path),
            ("workflow_db_path", self.workflow_db_path),
            ("eventbus_db_path", self.eventbus_db_path),
        ):
            parent = Path(path_str).parent
            if not parent.exists():
                raise ValueError(f"{label} parent directory does not exist: {parent}")


def build_db_config() -> DbConfig:
    """Construct DbConfig from common.toml; raises ValueError if common.toml is missing or malformed."""
    cfg = ConfigLoader().load("common.toml")
    return DbConfig(
        rag_db_path=cfg.get("rag_db_path", ""),
        session_db_path=cfg.get("session_db_path", ""),
        workflow_db_path=cfg.get("workflow_db_path", "/opt/llm/db/workflow.sqlite"),
        eventbus_db_path=cfg.get("eventbus_db_path", "/opt/llm/db/eventbus.sqlite"),
        sqlite_vec_so=cfg.get("sqlite_vec_so", ""),
        sqlite_timeout=int(cfg.get("sqlite_timeout", 30)),
        sqlite_busy_timeout_ms=int(cfg.get("sqlite_busy_timeout_ms", 30000)),
        embedding_dims=int(cfg.get("embedding_dims", 384)),
    )
