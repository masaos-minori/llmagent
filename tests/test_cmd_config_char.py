"""tests/test_cmd_config_char.py
Characterization tests for _ConfigMixin output methods.
Captures exact current output strings to preserve behavior during refactoring.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from agent.commands.cmd_config import _ConfigMixin
from agent.config import (
    ApprovalConfig,
    LLMConfig,
    MCPConfig,
    MemoryConfig,
    ObservabilityConfig,
    RAGConfig,
    ToolConfig,
)


class _Config(_ConfigMixin):
    def __init__(self, ctx: Any) -> None:
        self._ctx = ctx


def _make_ctx(**overrides: Any) -> Any:
    ctx = MagicMock()
    ctx.cfg.llm = overrides.get("llm", LLMConfig())
    ctx.cfg.rag = overrides.get("rag", RAGConfig())
    ctx.cfg.tool = overrides.get("tool", ToolConfig())
    ctx.cfg.mcp = overrides.get("mcp", MCPConfig())
    ctx.cfg.approval = overrides.get("approval", ApprovalConfig())
    ctx.cfg.memory = overrides.get("memory", MemoryConfig())
    ctx.cfg.observability = overrides.get("observability", ObservabilityConfig())
    ctx.conv.plan_mode = overrides.get("plan_mode", False)
    return ctx


class TestPrintConfigValues:
    """Characterization: _print_config_values output must not change."""

    def test_default_output(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "Settings:" in out
        assert "llm_url" in out
        assert "SSE stream settings:" in out
        assert "Execution settings:" in out
        assert "Semantic cache:" in out
        assert "MCP / security settings:" in out
        assert "Approval settings:" in out
        assert "Security settings (tool safety):" in out
        assert "plan_mode           : OFF" in out
        assert "risk_rules" in out
        assert "allowed_root        : (disabled)" in out

    def test_default_output_full(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        lines = [ln for ln in out.split("\n") if ln.strip()]
        assert len(lines) > 30
        assert lines[0] == "Settings:"
        assert "llm_url             :" in lines[1]

    def test_with_plan_mode_on(self, capsys: Any) -> None:
        ctx = _make_ctx(plan_mode=True)
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "plan_mode           : ON" in out

    def test_with_risk_rules_empty(self, capsys: Any) -> None:
        approval = ApprovalConfig()
        approval.approval_risk_rules = {}
        ctx = _make_ctx(approval=approval)
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "risk_rules          : (none)" in out

    def test_with_allowed_repos(self, capsys: Any) -> None:
        approval = ApprovalConfig()
        approval.approval_github_allowed_repos = ["owner/repo"]
        ctx = _make_ctx(approval=approval)
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "github_allowed_repos:" in out
        assert "Fail-Closed" not in out

    def test_with_allowed_tools(self, capsys: Any) -> None:
        tool = ToolConfig()
        tool.allowed_tools = ["read_file", "write_file"]
        ctx = _make_ctx(tool=tool)
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "allowed_tools" in out
        assert "unrestricted" not in out

    def test_with_plan_blocked_tools(self, capsys: Any) -> None:
        tool = ToolConfig()
        tool.plan_blocked_tools = ["write_file", "delete_file"]
        ctx = _make_ctx(tool=tool)
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "plan_blocked_tools  :" in out
        assert "    - write_file" in out

    def test_with_allowed_root(self, capsys: Any) -> None:
        approval = ApprovalConfig()
        approval.allowed_root = "/home/user/project"
        ctx = _make_ctx(approval=approval)
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        assert "allowed_root        : '/home/user/project'" in out

    def test_output_lines_match_snapshot(self, capsys: Any) -> None:
        ctx = _make_ctx()
        cmd = _Config(ctx)
        cmd._print_config_values()
        out = capsys.readouterr().out
        expected_snippets = [
            "Settings:",
            "  llm_url             : ",
            "  github_server_url   : http://127.0.0.1:8006",
            "  max_tool_turns      : 5",
            "  http_timeout        : 30.0s",
            "  context_char_limit  : 8000",
            "  context_compress    : 4 turn pairs",
            "  tool_cache_ttl      : 300.0s",
            "  llm_temperature     : 0.2",
            "SSE stream settings:",
            "  sse_heartbeat_timeout              : 30.0s",
            "  sse_malformed_retry                : 2",
            "Execution settings:",
            "  serial_tool_calls   : False",
            "  use_tool_summarize  : False",
            "Semantic cache:",
            "  use_semantic_cache  : False",
            "  sem_cache_threshold : 0.92",
            "MCP / security settings:",
            "  tool_def_strict     : False",
            "  watchdog_interval   : 30.0s",
            "Approval settings:",
            "  risk_rules          : ",
            "  protected_paths     :",
            "  high_risk_branches  :",
            "  dry_run_tools       :",
            "  masked_fields       :",
            "Security settings (tool safety):",
            "  allowed_root        : (disabled)",
            "  github_allowed_repos: (Fail-Closed",
            "  tool_safety_tiers   : 0 tools classified",
            "  allowed_tools       : (unrestricted)",
            "  plan_mode           : OFF",
            "  plan_blocked_tools  :",
            "    - write_file",
            "    - delete_file",
        ]
        for snippet in expected_snippets:
            assert snippet in out, f"expected {snippet!r} in output"
