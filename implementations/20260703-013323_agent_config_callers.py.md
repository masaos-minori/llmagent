# Implementation: scripts/agent/ — Update all callers of agent.config stub

**Plan source:** `plans/20260702-202739_plan.md` (Phase 2)
**Target file:** `scripts/agent/`

---

## Goal

Replace all imports from the `agent.config` compatibility stub with direct imports from `agent.config_dataclasses` or `agent.config_builders` across all affected script and test files so that the stub can safely be deleted.

---

## Scope

**In:**
- Update imports in these script files:
  - `scripts/agent/context.py`
  - `scripts/agent/tool_result_formatter.py`
  - `scripts/agent/tool_policy.py`
  - `scripts/agent/services/config_reload.py`
  - `scripts/agent/commands/cmd_config_display.py`
- Update imports in these test files:
  - `tests/test_tool_policy_comprehensive.py`
  - `tests/test_tool_policy.py`
  - `tests/test_tool_runner.py`
  - `tests/test_tool_approval_risk.py`
  - `tests/test_llm_client.py`
  - `tests/test_cmd_config_char.py`
  - `tests/test_config_loader.py`
  - `tests/test_tool_approval_repos.py`
  - `tests/test_tool_approval_preflight.py`
  - `tests/test_tool_result_formatter.py`
  - `tests/test_tool_approval_paths.py`
  - `tests/test_tool_audit.py`
  - `tests/test_rag_get_cfg.py`
  - `tests/test_tool_loop_guard.py`
  - `tests/test_plugin_ci_strict.py`
- Run `uv run pytest -x -q` after each file change

**Out:**
- Refactoring unrelated dependency boundaries
- Changing agent config behavior
- Introducing new tests beyond covering changed import paths

---

## Assumptions

1. All symbols previously re-exported by `agent/config.py` are available from either `agent.config_dataclasses` or `agent.config_builders`.
2. The specific mapping for each import (dataclasses vs builders) can be determined by inspecting the existing stub and the target modules.
3. Running `uv run pytest -x -q` after each file change is sufficient to catch regressions early.

---

## Implementation

### Target file

`scripts/agent/` (multiple files)

### Procedure

1. Inspect `scripts/agent/config.py` to understand what it re-exports and from which sub-module each symbol originates.
2. For each affected script file listed in Scope:
   a. Identify the exact `from agent.config import ...` line(s).
   b. Replace with `from agent.config_dataclasses import ...` or `from agent.config_builders import ...` as appropriate.
   c. Run `uv run pytest -x -q` to confirm no regressions.
3. Repeat step 2 for each affected test file.
4. After all files are updated, run a final grep to confirm no remaining references:
   `grep -rn "from agent.config import\|import agent.config" scripts/ tests/`

### Method

Edit tool for code changes in each target file.

### Details

- `agent/context.py` likely imports `build_agent_config` → redirect to `from agent.config_builders import build_agent_config`
- `agent/tool_result_formatter.py` likely imports `AgentConfig` → redirect to `from agent.config_dataclasses import AgentConfig`
- Each file must be updated individually, with a test run after each change to isolate regressions
- The stub file `scripts/agent/config.py` itself is NOT deleted in this phase (deletion occurs in Phase 6)

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| After each file | `uv run pytest -x -q` | all pass, no new failures |
| Grep residual imports | `grep -rn "from agent.config import\|import agent.config" scripts/ tests/` | 0 results |
| Lint | `ruff check scripts/agent/` | 0 errors |
| Type check | `mypy scripts/agent/` | no new errors |
| Tests | `uv run pytest` | all pass |
