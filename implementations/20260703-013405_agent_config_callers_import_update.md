# Implementation: scripts/agent/ — Update agent.config Stub Import Callers

**Plan source:** `plans/20260702-202739_plan.md` (Phase 2)
**Target file:** `scripts/agent/` (context.py, tool_policy.py, tool_result_formatter.py, config_reload.py, cmd_config_display.py + test files)

---

## Goal

Replace all `from agent.config import ...` statements in scripts and tests with direct imports from `agent.config_builders` or `agent.config_dataclasses`, as a prerequisite for deleting `scripts/agent/config.py`.

---

## Scope

**In:**
- `scripts/agent/context.py`: `build_agent_config` → `from agent.config_builders import`
- `scripts/agent/tool_policy.py`: `AgentConfig` (TYPE_CHECKING) → `from agent.config_dataclasses import`
- `scripts/agent/tool_result_formatter.py`: `AgentConfig` (TYPE_CHECKING) → `from agent.config_dataclasses import`
- `scripts/agent/services/config_reload.py` (line 382, deferred): `_build_mcp_servers` → `from agent.config_builders import`; keep `# noqa: PLC0415`
- `scripts/agent/commands/cmd_config_display.py` (line 216, deferred): `_CONFIG_DIR` → `from agent.config_builders import`; keep `# noqa: PLC0415`
- Test files: test_tool_policy_comprehensive.py, test_tool_policy.py, test_tool_runner.py, test_tool_approval_risk.py, test_llm_client.py, test_cmd_config_char.py, test_config_loader.py, test_tool_approval_repos.py, test_tool_approval_preflight.py, test_tool_result_formatter.py, test_tool_approval_paths.py, test_tool_audit.py, test_rag_get_cfg.py, test_tool_loop_guard.py, test_plugin_ci_strict.py

**Out:**
- Deleting `scripts/agent/config.py` (Phase 6 — separate step)
- Changing config dataclass or builder behavior

---

## Assumptions

1. Builder symbols: `build_agent_config`, `load_config`, `ConfigLoadError`, `_CONFIG_DIR`, `_build_mcp_servers` → `agent.config_builders`
2. Dataclass symbols: `AgentConfig`, `LLMConfig`, `RAGConfig`, `MemoryConfig`, `MCPConfig`, `ApprovalConfig`, `ObservabilityConfig`, `ToolConfig` → `agent.config_dataclasses`
3. When a file imports both kinds, split into two import lines.

---

## Implementation

### Target file

Multiple files under `scripts/agent/` and `tests/`

### Procedure

1. For each file, read the existing import from `agent.config`.
2. Categorize each symbol as builder or dataclass.
3. Replace with the appropriate sub-module import; preserve `# noqa` comments if present.
4. Run `uv run pytest -x -q` after each file change.

### Method

Edit tool for each file. Bash for intermediate pytest checks.

### Details

Example replacements:
- `from agent.config import AgentConfig, build_agent_config` → split into `from agent.config_dataclasses import AgentConfig` and `from agent.config_builders import build_agent_config`
- Deferred imports: keep inside function body; only change the module path

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Caller check | `grep -R "from agent.config import" --include="*.py" scripts/ tests/ | grep -v .venv` | 0 matches |
| Lint | `uv run ruff check scripts/ tests/` | 0 new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Full suite | `uv run pytest` | All pass |
