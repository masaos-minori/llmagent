# Implementation: Remove low-risk backward-compatibility remnants (Phase 1)

## Goal

Remove three backward-compatibility shims that are either unused by production code or purely internal aliases, with zero production call sites depending on them: `preflight_deny_reason()`, `probe_mcp_health()`, and the `_WORKFLOWS_DIR` internal alias.

## Scope

**In:**
- `scripts/agent/tool_policy.py`: delete `preflight_deny_reason()` (docstring says "Deprecated: use check_preflight() instead"; only referenced from test files)
- `scripts/agent/repl_health.py`: delete `probe_mcp_health()` (docstring says "Backward-compatible bool wrapper around `_probe_mcp_health_detail()`"; only referenced from test files)
- `scripts/agent/workflow/workflow_loader.py`: delete `_WORKFLOWS_DIR = WORKFLOWS_DIR  # internal alias kept for backward compat` (line 44); replace its single internal use (`self._dir = workflows_dir or _WORKFLOWS_DIR`) with `WORKFLOWS_DIR` directly
- `tests/test_tool_policy.py`, `tests/test_tool_policy_comprehensive.py`: remove test cases exercising `preflight_deny_reason`
- `tests/test_repl_health.py`: remove test cases exercising `probe_mcp_health`; if any of those tests exist purely to cover `_probe_mcp_health_detail()` behavior, keep equivalent coverage by calling `_probe_mcp_health_detail()` directly

**Out:**
- `check_preflight()` and `_probe_mcp_health_detail()` themselves — unchanged, they remain the canonical implementations
- No changes to `WorkflowLoader` behavior — `WORKFLOWS_DIR` (public name) stays; only the redundant private alias is removed

## Assumptions

1. `preflight_deny_reason()` has no callers outside `tests/test_tool_policy.py` and `tests/test_tool_policy_comprehensive.py` — confirmed via `grep -rn "preflight_deny_reason" --include="*.py"`.
2. `probe_mcp_health()` has no callers outside `tests/test_repl_health.py` — confirmed via `grep -rn "probe_mcp_health\b" --include="*.py"`.
3. `_WORKFLOWS_DIR` is referenced only within `scripts/agent/workflow/workflow_loader.py` itself (line 101) — confirmed via `grep -rn "_WORKFLOWS_DIR\b" --include="*.py"`.
4. No external plugin or script (outside this repo) imports these three names — cannot be verified from this repo; treated as accepted risk per the approved work plan (`plans/20260710-102535_plan.md`, Phase 1).

## Implementation

### Target file

1. `scripts/agent/tool_policy.py`
2. `scripts/agent/repl_health.py`
3. `scripts/agent/workflow/workflow_loader.py`
4. `tests/test_tool_policy.py`
5. `tests/test_tool_policy_comprehensive.py`
6. `tests/test_repl_health.py`

### Procedure

1. In `scripts/agent/tool_policy.py`, delete the `preflight_deny_reason()` function definition (currently defined right after `check_preflight()`).
2. In `scripts/agent/repl_health.py`, delete the `probe_mcp_health()` function definition (currently defined right after `_probe_mcp_health_detail()`).
3. In `scripts/agent/workflow/workflow_loader.py`, delete line `_WORKFLOWS_DIR = WORKFLOWS_DIR  # internal alias kept for backward compat` and change `self._dir = workflows_dir or _WORKFLOWS_DIR` to `self._dir = workflows_dir or WORKFLOWS_DIR`.
4. In each of the three test files, remove test functions/assertions that call the deleted functions directly; where a test's real intent was to cover the underlying non-deprecated function, rewrite it to call that function instead of deleting coverage outright.
5. Run `uv run ruff check scripts/agent/tool_policy.py scripts/agent/repl_health.py scripts/agent/workflow/workflow_loader.py` — expect 0 errors.
6. Run `uv run mypy scripts/agent/tool_policy.py scripts/agent/repl_health.py scripts/agent/workflow/workflow_loader.py` — expect no new errors.
7. Run `grep -rn "preflight_deny_reason\|probe_mcp_health\|_WORKFLOWS_DIR" --include="*.py"` — expect 0 matches across the whole repo.

### Method

Direct deletion — no refactor of call sites needed since production code never called these three names.

### Details

- `preflight_deny_reason()` wraps `check_preflight()` in a try/except and returns `(audit_decision, message) | None` instead of raising `PolicyViolationError`. Its docstring already states it is deprecated in favor of `check_preflight()`.
- `probe_mcp_health()` wraps `_probe_mcp_health_detail()` and collapses the structured `McpHealthProbeResult` into a plain `bool`. Production code (e.g. `check_service_health()`) already calls `_probe_mcp_health_detail()` directly.
- `_WORKFLOWS_DIR` duplicates `WORKFLOWS_DIR` under a private name with no distinct behavior; it exists only inside `WorkflowLoader.__init__`.

## Validation plan

```bash
uv run ruff check scripts/agent/tool_policy.py scripts/agent/repl_health.py scripts/agent/workflow/workflow_loader.py
uv run mypy scripts/agent/tool_policy.py scripts/agent/repl_health.py scripts/agent/workflow/workflow_loader.py
PYTHONPATH=scripts uv run lint-imports
uv run pytest tests/test_tool_policy.py tests/test_tool_policy_comprehensive.py tests/test_repl_health.py -v
grep -rn "preflight_deny_reason\|probe_mcp_health\|_WORKFLOWS_DIR" --include="*.py"   # expect no output
```

Expected outcome: all listed tests pass, no lint/type regressions, and the three removed names produce zero grep hits anywhere in the repository.
