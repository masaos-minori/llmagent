#!/usr/bin/env python3
"""db/config.py
DbConfig dataclass and builder for SQLite + embedding service paths.

Separated from agent/config.py so that db/ layer modules can reference
database configuration without importing from agent/.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from shared.config_loader import ConfigLoader


@dataclass
class DbConfig:
    """Immutable configuration for the SQLite database and embedding service."""

    rag_db_path: str
    session_db_path: str
    sqlite_vec_so: str
    embed_url: str
    sqlite_timeout: int = 30
    sqlite_busy_timeout_ms: int = 30000
    embedding_dims: int = 384

    def __post_init__(self) -> None:
        if not self.rag_db_path:
            raise ValueError("rag_db_path must not be empty")
        if not self.session_db_path:
            raise ValueError("session_db_path must not be empty")
        if not self.sqlite_vec_so:
            raise ValueError("sqlite_vec_so must not be empty")
        if not self.embed_url:
            raise ValueError("embed_url must not be empty")
        if self.sqlite_timeout < 1:
            raise ValueError(f"sqlite_timeout must be >= 1, got {self.sqlite_timeout}")
        if self.embedding_dims < 1:
            raise ValueError(f"embedding_dims must be >= 1, got {self.embedding_dims}")
        # DB files are created automatically by SQLite on first open;
        # validate that the parent directory exists rather than the file itself.
        for label, path_str in (
            ("rag_db_path", self.rag_db_path),
            ("session_db_path", self.session_db_path),
        ):
            parent = Path(path_str).parent
            if not parent.exists():
                raise ValueError(f"{label} parent directory does not exist: {parent}")
        # sqlite-vec is a shared library that must already exist.
        if not Path(self.sqlite_vec_so).exists():
            raise ValueError(f"sqlite_vec_so does not exist: {self.sqlite_vec_so}")


def build_db_config() -> DbConfig:
    """Construct DbConfig from common.toml configuration via ConfigLoader."""
    cfg = ConfigLoader().load_all()
    return DbConfig(
        rag_db_path=cfg.get("rag_db_path", ""),
        session_db_path=cfg.get("session_db_path", ""),
        sqlite_vec_so=cfg.get("sqlite_vec_so", ""),
        embed_url=cfg.get("embed_url", ""),
        sqlite_timeout=int(cfg.get("sqlite_timeout", 30)),
        sqlite_busy_timeout_ms=int(cfg.get("sqlite_busy_timeout_ms", 30000)),
        embedding_dims=int(cfg.get("embedding_dims", 384)),
    )
