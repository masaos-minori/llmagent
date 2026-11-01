"""tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py

RAGCORPUS001 REQ-002: ``_identity_payload()`` (scripts/mcp_servers/rag_pipeline/
rag_pipeline_server.py) returns the server's own corpus identity wire dict.

Locks the read-path contract behind the additive ``corpus_identity`` field:
  - an empty ``rag_db_path`` yields the unverified dict (never omitted);
  - a seeded corpus yields the verified seven-field dict;
  - a missing/unreadable corpus fails closed to the unverified dict (never raises).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
from mcp_servers.rag_pipeline import rag_pipeline_server as server
from mcp_servers.rag_pipeline.rag_pipeline_models import RagPipelineConfig
from rag.pipeline import SCHEMA_VERSION

_UNVERIFIED_KEYS = frozenset(
    {
        "corpus_id",
        "index_generation",
        "schema_version",
        "embedding_model_id",
        "normalization_version",
        "chunking_policy_version",
        "verified",
    }
)


def _seed_rag_corpus_meta(db_path: Path) -> None:
    """Create a temp RAG database with a single ``rag_corpus_meta`` row."""
    conn = sqlite3.connect(str(db_path))
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS rag_corpus_meta (
            corpus_id                TEXT    NOT NULL,
            index_generation         INTEGER NOT NULL,
            embedding_model_id       TEXT    NOT NULL,
            normalization_version    TEXT    NOT NULL,
            chunking_policy_version  TEXT    NOT NULL,
            updated_at               TEXT    NOT NULL,
            CHECK (rowid = 1)
        );
        """
    )
    conn.execute(
        "INSERT INTO rag_corpus_meta "
        "(corpus_id, index_generation, embedding_model_id, "
        " normalization_version, chunking_policy_version, updated_at) "
        "VALUES ('seeded-corpus-id', 3, 'seed-embed-v2', '1', '1', datetime('now'))"
    )
    conn.commit()
    conn.close()


def _patch_cfg(
    monkeypatch: pytest.MonkeyPatch, *, rag_db_path: str, sqlite_vec_so: str = ""
) -> None:
    monkeypatch.setattr(
        server,
        "_cfg",
        RagPipelineConfig(rag_db_path=rag_db_path, sqlite_vec_so=sqlite_vec_so),
    )


class TestIdentityPayloadEmptyCorpus:
    def test_empty_rag_db_path_returns_unverified_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_cfg(monkeypatch, rag_db_path="")
        payload = server._identity_payload()
        assert set(payload) == _UNVERIFIED_KEYS
        assert payload["verified"] is False
        assert payload["corpus_id"] == ""
        assert payload["index_generation"] == 0
        assert payload["schema_version"] == SCHEMA_VERSION
        assert payload["embedding_model_id"] == ""


class TestIdentityPayloadSeededCorpus:
    def test_seeded_corpus_returns_verified_seven_field_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        db_path = tmp_path / "seeded.sqlite"
        _seed_rag_corpus_meta(db_path)
        _patch_cfg(monkeypatch, rag_db_path=str(db_path))

        payload: dict[str, Any] = server._identity_payload()

        assert set(payload) == _UNVERIFIED_KEYS
        assert payload["verified"] is True
        assert payload["corpus_id"] == "seeded-corpus-id"
        assert payload["index_generation"] == 3
        assert payload["embedding_model_id"] == "seed-embed-v2"
        assert payload["schema_version"] == SCHEMA_VERSION
        assert payload["normalization_version"] == "1"
        assert payload["chunking_policy_version"] == "1"


class TestIdentityPayloadUnreadableCorpus:
    def test_missing_db_file_fails_closed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_cfg(monkeypatch, rag_db_path=str(tmp_path / "missing.sqlite"))
        # Must not raise even though the corpus is unreadable.
        payload = server._identity_payload()
        assert set(payload) == _UNVERIFIED_KEYS
        assert payload["verified"] is False
