"""Effective-configuration snapshot of the real ``config/agent.toml`` (agentcfg005 row 13).

Pins the deployment contract for the registered configuration fields: the
inventory measured at execution time is 18 explicit values equal to their code
defaults, 12 differing, and 3 registered fields absent from the file
(``tool.disabled_tools``, ``approval.gitops_push_blocked``,
``approval.approval_medium_preview_fallback``). An explicit value that equals its
code default must stay in the file (REQ-005), so the test fails if such a value is
dropped. The precedence case proves an explicit value wins over the code default.

Inventory scope: the values registered in ``scripts/agent/services/config_field_registry.py``
(33 entries after cliplc001 registered ``approval_medium_preview_fallback`` and
after the two prompt entries were removed by row 07). Counts were re-measured
against the current source on 2026-11-25 and match the recorded contract.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest
from agent import config_dataclasses as dc
from agent.config_builders import build_agent_config
from agent.services.config_field_registry import _CONFIG_ENTRIES
from shared.config_loader import ConfigLoader

# Recorded inventory (contract, not the pre-change measurement).
RECORDED_EQUAL_COUNT = 18
RECORDED_DIFFERING_COUNT = 12
RECORDED_DIFFERING_FIELDS = frozenset(
    {
        "approval.allowed_root",
        "approval.approval_high_risk_branches",
        "approval.approval_shell_safe_prefixes",
        "llm.context_token_limit",
        "llm.http_timeout",
        "llm.llm_max_tokens",
        "llm.llm_url",
        "llm.sse_heartbeat_timeout",
        "llm.sse_reconnect_max",
        "memory.memory_embed_url",
        "tool.allowed_tools",
        "tool.plan_blocked_tools",
    }
)
RECORDED_ABSENT_FIELDS = frozenset(
    {
        "approval.approval_medium_preview_fallback",
        "approval.gitops_push_blocked",
        "tool.disabled_tools",
    }
)

_SECTION_CLASS = {
    "approval": "ApprovalConfig",
    "llm": "LLMConfig",
    "memory": "MemoryConfig",
    "tool": "ToolConfig",
}

# MCP server entries reference environment variables; set them so the builders
# resolve without touching the recorded inventory (none of these keys is a
# registered field).
_ENV_REFS = (
    "MCP_SHELL_AUTH_TOKEN",
    "MCP_GIT_AUTH_TOKEN",
    "MCP_WEB_SEARCH_AUTH_TOKEN",
    "MCP_FILE_DELETE_AUTH_TOKEN",
    "MCP_FILE_WRITE_AUTH_TOKEN",
    "MCP_FILE_READ_AUTH_TOKEN",
    "MCP_GITHUB_AUTH_TOKEN",
    "MCP_CICD_AUTH_TOKEN",
    "MCP_RAG_PIPELINE_AUTH_TOKEN",
    "MCP_MDQ_AUTH_TOKEN",
)


def _default_for(cls: type, name: str) -> object:
    for field in dataclasses.fields(cls):
        if field.name == name:
            if field.default_factory is not dataclasses.MISSING:
                return field.default_factory()
            return field.default
    return None


def _classify(cfg: dict) -> tuple[set[str], set[str], set[str]]:
    """Classify every registered field as equal-to-default, differing, or absent."""
    effective = build_agent_config(dict(cfg))
    equal: set[str] = set()
    differing: set[str] = set()
    absent: set[str] = set()
    for entry in _CONFIG_ENTRIES:
        section = entry.section_path
        cls = getattr(dc, _SECTION_CLASS[section])
        if entry.name not in cfg:
            # Recorded as an assertion, not an error (Plan UNK-05).
            absent.add(f"{section}.{entry.name}")
            continue
        effective_value = getattr(getattr(effective, section), entry.name)
        default = _default_for(cls, entry.name)
        (equal if effective_value == default else differing).add(
            f"{section}.{entry.name}"
        )
    return equal, differing, absent


@pytest.mark.integration
def test_effective_config_snapshot_inventory(monkeypatch) -> None:
    """Real config/agent.toml resolves to the recorded inventory (REQ-008, AC-5)."""
    for name in _ENV_REFS:
        monkeypatch.setenv(name, "snapshot-test-token")

    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    cfg = ConfigLoader(config_dir=config_dir).load_all(strict=True)

    equal, differing, absent = _classify(cfg)

    assert len(equal) == RECORDED_EQUAL_COUNT
    assert differing == set(RECORDED_DIFFERING_FIELDS)
    assert len(differing) == RECORDED_DIFFERING_COUNT
    assert absent == set(RECORDED_ABSENT_FIELDS)


@pytest.mark.integration
def test_explicit_value_takes_precedence_over_code_default(monkeypatch) -> None:
    """An explicit value differing from the code default survives the builders."""
    for name in _ENV_REFS:
        monkeypatch.setenv(name, "snapshot-test-token")

    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    cfg = ConfigLoader(config_dir=config_dir).load_all(strict=True)

    # A field from the recorded differing group: explicit value must win.
    explicit = cfg["http_timeout"]
    assert explicit != 30.0  # the code default; guard the test's premise
    effective = build_agent_config(dict(cfg))
    assert effective.llm.http_timeout == explicit
