"""tests/db/test_db_config.py

Regression coverage for the workflow_db_path configuration contract
(adrchk019 REQ-003 / REQ-004):
- the repository ``config/agent.toml`` carries the ``workflow_db_path`` key and
  ``build_db_config()`` reads it back (no code fallback in play)
- ``scripts/db/config.py`` contains exactly one ``"/opt/llm/db/workflow.sqlite"``
  literal: the ``DbConfig`` field default

The read-back compares against the config file the loader actually resolves, so
the assertion holds under the conftest isolation rewrite (the isolated copy is a
rewritten copy of the repo ``agent.toml``; the repo-key presence is asserted
against the repo file directly).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

from db.config import build_db_config
from shared.config_loader import ConfigLoader

_REPO_ROOT = Path(__file__).resolve().parents[2]
_AGENT_TOML = _REPO_ROOT / "config" / "agent.toml"
_CONFIG_PY = _REPO_ROOT / "scripts" / "db" / "config.py"
_WORKFLOW_LITERAL = '"/opt/llm/db/workflow.sqlite"'


class TestWorkflowDbPathConfig:
    def test_build_db_config_reads_workflow_path_from_agent_toml(self) -> None:
        repo_cfg = tomllib.loads(_AGENT_TOML.read_text(encoding="utf-8"))
        assert "workflow_db_path" in repo_cfg
        cfg = build_db_config()
        loaded = ConfigLoader().load("agent.toml")
        assert cfg.workflow_db_path == loaded["workflow_db_path"]

    def test_single_default_literal(self) -> None:
        assert _CONFIG_PY.read_text(encoding="utf-8").count(_WORKFLOW_LITERAL) == 1
