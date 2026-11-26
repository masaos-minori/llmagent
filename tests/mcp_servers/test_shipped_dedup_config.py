"""tests/mcp_servers/test_shipped_dedup_config.py

The real `[dedup]` tables shipped under `config/*_mcp_server.toml` load through the
typed validator, set `pending_timeout_minutes` explicitly, and keep the default
config fingerprint (so the dedup store identity does not change).
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import pytest
from shared.config_errors import ConfigParseError
from shared.mcp_dedup import DedupStoreConfig, load_dedup_section
from shared.mcp_dedup_config import DB_DIR_ENV_VAR, _config_fingerprint

_CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"

_EXPECTED_SERVERS = frozenset(
    {
        "cicd",
        "file_delete",
        "file_read",
        "file_write",
        "git",
        "github",
        "mdq",
        "rag_pipeline",
        "shell",
        "web_search",
    }
)


def _shipped_dedup_tables() -> dict[str, dict[str, Any]]:
    tables: dict[str, dict[str, Any]] = {}
    for path in sorted(_CONFIG_DIR.glob("*_mcp_server.toml")):
        with path.open("rb") as handle:
            data = tomllib.load(handle)
        if "dedup" in data:
            tables[path.name] = data["dedup"]
    return tables


_TABLES = _shipped_dedup_tables()


@pytest.fixture(autouse=True)
def _canonical_db_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    """The shipped `db_path` is the production path, so no override may apply."""
    monkeypatch.delenv(DB_DIR_ENV_VAR, raising=False)


def test_the_shipped_tables_are_the_expected_servers() -> None:
    discovered = {name.removesuffix("_mcp_server.toml") for name in _TABLES}
    assert discovered == _EXPECTED_SERVERS


@pytest.mark.parametrize("filename", sorted(_TABLES))
def test_the_shipped_table_loads_through_the_validator(filename: str) -> None:
    config = load_dedup_section(_TABLES[filename], filename)

    assert isinstance(config, DedupStoreConfig)


@pytest.mark.parametrize("filename", sorted(_TABLES))
def test_pending_timeout_minutes_is_explicit(filename: str) -> None:
    assert "pending_timeout_minutes" in _TABLES[filename]


@pytest.mark.parametrize("filename", sorted(_TABLES))
def test_the_shipped_table_keeps_the_default_store_identity(filename: str) -> None:
    config = load_dedup_section(_TABLES[filename], filename)

    assert _config_fingerprint(config) == _config_fingerprint(DedupStoreConfig())


@pytest.mark.parametrize("filename", sorted(_TABLES))
def test_an_unknown_key_in_a_shipped_table_is_rejected(filename: str) -> None:
    table = {**_TABLES[filename], "sentinel_mode": 1}

    with pytest.raises(ConfigParseError, match="unknown dedup keys"):
        load_dedup_section(table, filename)
