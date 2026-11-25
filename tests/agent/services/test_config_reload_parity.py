"""tests/agent/services/test_config_reload_parity.py

AC-1 parity contract: one value table run through both entry points — the startup
build (`build_agent_config`) and the ``/reload`` path (`ConfigReloadService`) —
asserting identical accept and reject results and the same field-level error text
(REQ-001, REQ-002). A divergence between the two paths is a test failure here
rather than a documented difference.

The table also pins the ``allow_empty`` value chosen for each list entry (row 4)
and records the Plan's ``Newly rejected inputs`` list as the review surface for
the strictness change (UNK-01).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.services.config_field_registry import CONFIG_FIELD_REGISTRY
from agent.services.config_reload import ConfigReloadService
from agent.services.exceptions import ConfigReloadValidationError

from tests.agent._config_test_defaults import (
    MIN_MCP_SERVERS,
    SHIPPED_DB_PATH_KEYS,
)

# ---------------------------------------------------------------------------
# Value table: (section, field, value)
#
# Accept rows are values the strict rules accept and that differ from the live
# value, so an accepted change is observable in the outcome report.
# ---------------------------------------------------------------------------

_ACCEPT_ROWS: list[tuple[str, str, Any]] = [
    # llm section
    ("llm", "llm_url", "http://llm.local:8080"),
    ("llm", "llm_url", ""),
    ("llm", "http_timeout", 45.0),
    ("llm", "llm_retry_base_delay", 2.5),
    ("llm", "llm_temperature", 0.5),
    ("llm", "llm_max_tokens", 512),
    ("llm", "sse_heartbeat_timeout", 60.0),
    ("llm", "sse_malformed_retry", 3),
    ("llm", "sse_reconnect_max", 2),
    ("llm", "llm_stream_retry_on_heartbeat_timeout", False),
    ("llm", "llm_stream_retry_on_malformed_chunk", True),
    # tool section
    ("tool", "max_tool_turns", 9),
    ("tool", "tool_result_max_llm_chars", 6000),
    ("tool", "serial_tool_calls", True),
    ("tool", "plan_blocked_tools", ["write_file", "shell_run"]),
    ("tool", "plan_blocked_tools", []),
    ("tool", "allowed_tools", ["read_text_file", "list_directory"]),
    ("tool", "tool_policy_mode", "explicit_allowlist"),
    ("tool", "disabled_tools", ["shell_run", "write_file"]),
    # approval section
    ("approval", "allowed_root", "/srv/llm"),
    ("approval", "approval_protected_paths", ["/etc/", "/var/"]),
    ("approval", "approval_protected_paths", []),
    ("approval", "approval_high_risk_branches", ["main", "release"]),
    ("approval", "approval_shell_safe_prefixes", ["ls", "git status"]),
    ("approval", "approval_github_allowed_repos", ["owner/repo"]),
    # memory section
    ("memory", "memory_embed_url", "http://127.0.0.1:9000"),
    ("memory", "memory_max_pinned", 5),
    ("memory", "memory_local_only", True),
    ("memory", "memory_retention_days", 45),
]

# Reject rows: the Plan's "Newly rejected inputs" list, plus the inputs the old
# reload path already rejected, so a regression in either direction shows up here.
_REJECT_ROWS: list[tuple[str, str, Any]] = [
    # llm section
    ("llm", "llm_url", 7),
    ("llm", "llm_url", True),
    ("llm", "llm_url", "   "),
    ("llm", "http_timeout", "30"),
    ("llm", "http_timeout", True),
    ("llm", "llm_retry_base_delay", True),
    ("llm", "llm_temperature", True),
    ("llm", "llm_max_tokens", "512"),
    ("llm", "llm_max_tokens", True),
    ("llm", "sse_heartbeat_timeout", "30"),
    ("llm", "sse_malformed_retry", True),
    ("llm", "sse_reconnect_max", "1"),
    ("llm", "llm_stream_retry_on_heartbeat_timeout", 1),
    ("llm", "llm_stream_retry_on_malformed_chunk", "false"),
    # tool section
    ("tool", "max_tool_turns", "5"),
    ("tool", "max_tool_turns", True),
    ("tool", "tool_result_max_llm_chars", "4000"),
    ("tool", "tool_result_max_llm_chars", True),
    ("tool", "serial_tool_calls", 1),
    ("tool", "serial_tool_calls", "false"),
    ("tool", "plan_blocked_tools", 5),
    ("tool", "plan_blocked_tools", "write_file"),
    ("tool", "plan_blocked_tools", [1]),
    ("tool", "allowed_tools", "read_file"),
    ("tool", "tool_policy_mode", 7),
    ("tool", "tool_policy_mode", "explicit"),
    ("tool", "disabled_tools", 5),
    ("tool", "disabled_tools", "shell_execute"),
    # approval section
    ("approval", "allowed_root", 7),
    ("approval", "allowed_root", ""),
    ("approval", "approval_protected_paths", 5),
    ("approval", "approval_protected_paths", "/etc/"),
    ("approval", "approval_protected_paths", [1]),
    ("approval", "approval_high_risk_branches", 5),
    ("approval", "approval_high_risk_branches", "main"),
    ("approval", "approval_shell_safe_prefixes", 5),
    ("approval", "approval_shell_safe_prefixes", "ls"),
    ("approval", "approval_github_allowed_repos", 5),
    ("approval", "approval_github_allowed_repos", "owner/repo"),
    ("approval", "gitops_push_blocked", "true"),
    ("approval", "gitops_push_blocked", 1),
    ("approval", "approval_medium_preview_fallback", "true"),
    ("approval", "approval_medium_preview_fallback", 1),
    # memory section
    ("memory", "memory_embed_url", 7),
    ("memory", "memory_embed_url", "   "),
    ("memory", "memory_embed_enabled", 1),
    ("memory", "memory_embed_enabled", "false"),
    ("memory", "memory_max_pinned", "10"),
    ("memory", "memory_max_pinned", True),
    ("memory", "memory_local_only", 1),
    ("memory", "memory_local_only", "false"),
    ("memory", "memory_retention_days", "30"),
    ("memory", "memory_retention_days", True),
    ("memory", "use_memory_layer", "true"),
    ("memory", "use_memory_layer", 1),
    # startup-only fields: the type rule rejects them on both paths too
    ("llm", "context_token_limit", "0"),
    ("llm", "context_token_limit", True),
    ("llm", "context_char_limit", "8000"),
    ("llm", "context_char_limit", True),
    ("llm", "context_compress_turns", "4"),
    ("llm", "context_compress_turns", True),
]

# Startup-only rows: a valid value the startup build accepts and reads once, and
# that `/reload` must report as pending instead of writing into live state (REQ-003).
_STARTUP_ONLY_ROWS: list[tuple[str, str, Any]] = [
    ("llm", "context_token_limit", 4096),
    ("llm", "context_char_limit", 12000),
    ("llm", "context_compress_turns", 6),
    ("approval", "approval_medium_preview_fallback", False),
    ("approval", "gitops_push_blocked", True),
    ("memory", "use_memory_layer", False),
    ("memory", "memory_embed_enabled", False),
]

# Live (startup-built) values every row is compared against. They are deliberately
# different from the accepted values above, so an accepted change is observable in
# the outcome report instead of hidden by a no-op candidate.
_LLM_LIVE: dict[str, Any] = {
    "llm_url": "http://llm.local:8000",
    "http_timeout": 30.0,
    "llm_retry_base_delay": 1.0,
    "llm_temperature": 0.2,
    "llm_max_tokens": 1024,
    "sse_heartbeat_timeout": 30.0,
    "sse_malformed_retry": 2,
    "sse_reconnect_max": 1,
    "llm_stream_retry_on_heartbeat_timeout": True,
    "llm_stream_retry_on_malformed_chunk": False,
    "context_token_limit": 0,
    "context_char_limit": 8000,
    "context_compress_turns": 4,
}
_TOOL_LIVE: dict[str, Any] = {
    "max_tool_turns": 5,
    "tool_result_max_llm_chars": 4000,
    "serial_tool_calls": False,
    "plan_blocked_tools": ["write_file"],
    "allowed_tools": ["read_file"],
    "tool_policy_mode": "discovered",
    "disabled_tools": ["shell_run"],
}
_APPROVAL_LIVE: dict[str, Any] = {
    "allowed_root": "/opt/llm",
    "approval_protected_paths": ["/etc/"],
    "approval_high_risk_branches": ["main"],
    "approval_shell_safe_prefixes": ["ls"],
    "approval_github_allowed_repos": [],
    "approval_medium_preview_fallback": True,
    "gitops_push_blocked": False,
}
_MEMORY_LIVE: dict[str, Any] = {
    "use_memory_layer": True,
    "memory_embed_url": "http://127.0.0.1:8100",
    "memory_embed_enabled": True,
    "memory_retention_days": 90,
    "memory_max_pinned": 10,
    "memory_local_only": False,
}


@pytest.fixture(autouse=True)
def prompt_source_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Point the prompt reader at a fixture source that matches the live value.

    The reload path reads prompt content through ``agent.prompt_source``; the
    fixture content equals the ctx value so a reload mutates nothing but the row
    under test.
    """
    manifest_dir = tmp_path / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    (manifest_dir / "prompt_source.toml").write_text(
        'default = "fixture default prompt"\n', encoding="utf-8"
    )
    monkeypatch.setenv("LLMAGENT_REGISTRY_DIR", str(tmp_path))


def _startup_payload(**overrides: Any) -> dict[str, Any]:
    """The complete payload the startup entry point builds the fixture config from."""
    payload: dict[str, Any] = {
        **_LLM_LIVE,
        **_TOOL_LIVE,
        **_APPROVAL_LIVE,
        **_MEMORY_LIVE,
        **SHIPPED_DB_PATH_KEYS,
        "mcp_servers": MIN_MCP_SERVERS,
    }
    payload.update(overrides)
    return payload


def _startup_build(**overrides: Any) -> AgentConfig:
    """Run the startup entry point on the fixture payload with the row's override."""
    return build_agent_config(cfg_override=_startup_payload(**overrides))


def _make_ctx(**overrides: Any) -> MagicMock:
    """Build a reload ctx whose live config is what the startup entry point builds."""
    ctx = MagicMock()
    ctx.cfg = _startup_build(**overrides)
    ctx.conv.system_prompt_name = "default"
    ctx.conv.system_prompt_content = "fixture default prompt"
    for service in (
        "llm",
        "hist_mgr",
        "runtime_tools",
        "memory",
        "embedding",
        "retriever",
        "lifecycle",
    ):
        setattr(ctx.services_required, service, None)
    return ctx


def _reload(ctx: MagicMock, **overrides: Any) -> Any:
    """Run the reload path on a partial payload, as the CLI payload shape requires."""
    return ConfigReloadService(ctx).apply_config_dict(overrides)


def _live_value(ctx: MagicMock, section: str, field: str) -> Any:
    return getattr(getattr(ctx.cfg, section), field)


def _path_result(run: Any) -> tuple[str, str]:
    """Reduce one path's outcome to ("accept", "") or ("reject", error text).

    Both paths raise a `ValueError` for a rejected value; the exact class is the
    subject of Plan row 12 (R4), so this contract compares the text only.
    """
    try:
        run()
    except ValueError as exc:
        return ("reject", str(exc))
    return ("accept", "")


class TestStartupReloadAcceptParity:
    """AC-1: every value the startup path accepts, the reload path also accepts."""

    @pytest.mark.parametrize(
        "section,field,value",
        _ACCEPT_ROWS,
        ids=[f"{s}-{f}-{v}" for s, f, v in _ACCEPT_ROWS],
    )
    def test_both_paths_accept_and_apply(
        self, section: str, field: str, value: Any
    ) -> None:
        built = _startup_build(**{field: value})
        assert getattr(getattr(built, section), field) == value

        ctx = _make_ctx()
        outcome = _reload(ctx, **{field: value})
        assert section in outcome.applied
        assert _live_value(ctx, section, field) == value

    def test_empty_list_has_the_same_result_on_both_paths_for_every_entry(self) -> None:
        """Row 4: `allow_empty` is the single source of the empty-list decision."""
        entries = sorted(
            name
            for name, entry in CONFIG_FIELD_REGISTRY.items()
            if getattr(entry.field_type, "name", "") in ("str_list", "int_list")
        )
        assert entries
        for name in entries:
            startup = _path_result(lambda: _startup_build(**{name: []}))
            reload = _path_result(lambda: _reload(_make_ctx(), **{name: []}))
            assert startup == reload, name


class TestStartupReloadRejectParity:
    """AC-1: every value the startup path rejects, the reload path also rejects,
    with the same field-level message."""

    @pytest.mark.parametrize(
        "section,field,value",
        _REJECT_ROWS,
        ids=[f"{s}-{f}-{v}" for s, f, v in _REJECT_ROWS],
    )
    def test_both_paths_reject_with_the_same_message(
        self, section: str, field: str, value: Any
    ) -> None:
        with pytest.raises(ValueError) as startup_exc:
            _startup_build(**{field: value})
        with pytest.raises(ValueError) as reload_exc:
            _reload(_make_ctx(), **{field: value})

        # The startup path reports every error it found in one list; the reload
        # path reports the field it was asked to change. The field-level text is
        # identical because both call the same rule.
        assert str(reload_exc.value) in str(startup_exc.value)

    @pytest.mark.parametrize(
        "section,field,value",
        _REJECT_ROWS,
        ids=[f"{s}-{f}-{v}" for s, f, v in _REJECT_ROWS],
    )
    def test_rejected_value_leaves_live_state_untouched(
        self, section: str, field: str, value: Any
    ) -> None:
        ctx = _make_ctx()
        live = _live_value(ctx, section, field)
        with pytest.raises(ConfigReloadValidationError):
            _reload(ctx, **{field: value})
        assert _live_value(ctx, section, field) == live

    def test_type_rule_message_does_not_echo_the_value(self) -> None:
        """REQ-011: a rejected value is not put into the message the CLI prints."""
        ctx = _make_ctx()
        secret = "do-not-echo-this-value"
        with pytest.raises(ConfigReloadValidationError) as exc_info:
            _reload(ctx, allowed_root=secret)
        assert secret not in str(exc_info.value)
        assert "allowed_root" in str(exc_info.value)


class TestStartupOnlyFields:
    """Startup-only fields: startup reads the value, reload reports it as pending."""

    @pytest.mark.parametrize(
        "section,field,value",
        _STARTUP_ONLY_ROWS,
        ids=[f"{s}-{f}-{v}" for s, f, v in _STARTUP_ONLY_ROWS],
    )
    def test_startup_builds_and_reload_reports_without_applying(
        self, section: str, field: str, value: Any
    ) -> None:
        built = _startup_build(**{field: value})
        assert getattr(getattr(built, section), field) == value

        ctx = _make_ctx()
        live = _live_value(ctx, section, field)
        outcome = _reload(ctx, **{field: value})
        assert field in outcome.startup_only
        assert section not in outcome.applied
        assert _live_value(ctx, section, field) == live

    def test_every_registry_entry_is_covered_by_the_table(self) -> None:
        """Registry drift shows up here: a new entry must join the right row group."""
        hot = {name for name, e in CONFIG_FIELD_REGISTRY.items() if e.hot_reloadable}
        startup_only = {
            name for name, e in CONFIG_FIELD_REGISTRY.items() if not e.hot_reloadable
        }
        covered_hot = {f for _, f, _ in _ACCEPT_ROWS} | {f for _, f, _ in _REJECT_ROWS}
        covered_startup = {f for _, f, _ in _STARTUP_ONLY_ROWS} | {
            f for _, f, _ in _REJECT_ROWS
        }
        assert hot == covered_hot & hot
        assert startup_only == covered_startup & startup_only


class TestShippedConfiguration:
    """No shipped configuration file contains an input the strict rules now reject (UNK-01)."""

    def _shipped_raw(self) -> dict[str, Any]:
        from shared.config_loader import ConfigLoader

        config_dir = Path(__file__).resolve().parents[3] / "config"
        return ConfigLoader(config_dir=config_dir).load_all()

    def test_shipped_config_builds_without_error(self) -> None:
        build_agent_config(cfg_override=self._shipped_raw())

    def test_shipped_config_reloads_with_no_change(self) -> None:
        raw = self._shipped_raw()
        ctx = _make_ctx()
        ctx.cfg = build_agent_config(cfg_override=raw)

        outcome = ConfigReloadService(ctx).apply_config_dict(raw)
        assert outcome.applied == []
        assert outcome.needs_restart == []
        assert outcome.startup_only == []
