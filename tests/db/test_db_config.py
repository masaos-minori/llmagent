"""tests/db/test_db_config.py

Regression coverage for the workflow_db_path configuration contract
(adrchk019 REQ-003 / REQ-004):
- the repository ``config/agent.toml`` carries the ``workflow_db_path`` key
- ``build_db_config()`` resolves the mapping the owning process supplies, including
  that key, and rejects a malformed one; it reads no configuration file itself
- ``scripts/db/config.py`` contains exactly one ``"/opt/llm/db/workflow.sqlite"``
  literal: the ``DbConfig`` field default
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path

import pytest
from db.config import build_db_config

_REPO_ROOT = Path(__file__).resolve().parents[2]

_AGENT_TOML = _REPO_ROOT / "config" / "agent.toml"

_CONFIG_PY = _REPO_ROOT / "scripts" / "db" / "config.py"

_WORKFLOW_LITERAL = '"/opt/llm/db/workflow.sqlite"'


def _mapping(root: Path) -> dict:
    """A supplied mapping shaped like the file the owning process loads."""
    return {
        "rag_db_path": str(root / "rag.sqlite"),
        "session_db_path": str(root / "session.sqlite"),
        "workflow_db_path": str(root / "workflow.sqlite"),
        "sqlite_vec_so": str(root / "vec0.so"),
    }


class TestWorkflowDbPathConfig:
    def test_repo_config_carries_the_workflow_path_key(self) -> None:
        repo_cfg = tomllib.loads(_AGENT_TOML.read_text(encoding="utf-8"))
        assert "workflow_db_path" in repo_cfg

    def test_build_db_config_resolves_the_supplied_mapping(
        self, tmp_path: Path
    ) -> None:
        supplied = _mapping(tmp_path)
        cfg = build_db_config(supplied)
        assert cfg.workflow_db_path == supplied["workflow_db_path"]
        assert cfg.rag_db_path == supplied["rag_db_path"]
        assert cfg.session_db_path == supplied["session_db_path"]

    def test_missing_workflow_key_falls_back_to_the_field_default(
        self, tmp_path: Path
    ) -> None:
        supplied = _mapping(tmp_path)
        del supplied["workflow_db_path"]
        cfg = build_db_config(supplied)
        # conftest.py redirects the default "/opt/llm/db/workflow.sqlite" into the
        # isolation root, so what is asserted here is that the field default is the
        # value used when the mapping does not carry the key.
        isolation_root = os.environ["LLMAGENT_TEST_ROOT"]
        assert cfg.workflow_db_path == f"{isolation_root}/db/workflow.sqlite"

    def test_non_integer_sqlite_timeout_is_rejected(self, tmp_path: Path) -> None:
        supplied = _mapping(tmp_path)
        supplied["sqlite_timeout"] = "30"
        with pytest.raises(ValueError, match="sqlite_timeout"):
            build_db_config(supplied)

    def test_empty_vec_so_is_rejected_naming_the_key(self, tmp_path: Path) -> None:
        supplied = _mapping(tmp_path)
        supplied["sqlite_vec_so"] = ""
        with pytest.raises(ValueError, match="sqlite_vec_so"):
            build_db_config(supplied)

    def test_single_default_literal(self) -> None:
        assert _CONFIG_PY.read_text(encoding="utf-8").count(_WORKFLOW_LITERAL) == 1
