# Refactor repl_health.py — separation of concerns

## Priority
Medium

## Summary
Split `scripts/agent/repl_health.py` (666 lines) into focused modules to reduce the size of `audit_security_defaults()` (~212 lines, the file's largest function) and clarify the boundaries between the five distinct concerns currently combined in one file: MCP service health checks, tool-definition validation, workflow schema/definition validation, routing-drift validation, and security-defaults auditing.

## Background
The module docstring states it was "Extracted from agent/repl.py to allow targeted loading when modifying health check behaviour," but after extraction it continued to accumulate independent validation concerns rather than being split further. A similar split was already completed for `scripts/agent/orchestrator.py` (`issues/done/20260829-080923_refactor_001_orchestrator_separation.md`, 764 → ~300 lines across six extracted classes) and for `scripts/agent/repl.py` (`issues/done/20260829-080924_refactor_002_repl_separation.md`). `repl_health.py` was not in scope for either of those and remains unsplit.

## Problem
`scripts/agent/repl_health.py` mixes at least five independent concerns in one 666-line file:

1. **MCP service health checks** — `_probe_mcp_health_detail`, `check_service_health`, `check_readiness`
2. **Tool-definition validation** — `_validate_tools_response`, `_collect_server_tool_names`, `_check_tool_definitions`, `check_tool_definitions_runtime`
3. **Workflow schema/definition validation** — `check_workflow_definition`, `check_workflow_schema`, `SchemaCheckResult`, `REQUIRED_WORKFLOW_TABLES`
4. **Routing-drift validation** — `check_routing_drift`, `check_routing_safety_tiers`
5. **Security-defaults auditing** — `audit_security_defaults`, `_load_audit_config_or_warn`

`audit_security_defaults()` alone is roughly 212 lines (the bulk of the file) and inlines at least seven distinct checks (HTTP auth_token presence, shell sandbox backend/allowlist, git/github/cicd fail-closed allowlists, a `ProductionConfigValidator` call, and GitHub write-permission settings) in a single function body, making individual checks hard to test or modify in isolation. The companion test files (`tests/agent/test_repl_health.py`, 938 lines; `tests/agent/test_repl_health_malformed.py`, 126 lines — 1064 lines combined) mirror this lack of separation.

## Reason for Change
- Changing one security check inside `audit_security_defaults()` currently requires reviewing and re-testing the entire 212-line function, increasing the risk of an unrelated regression in a security-relevant code path.
- The five concerns have different callers, different failure semantics (some raise in production mode, some only warn), and different test setups, but are not separable at the module level.
- Following the same separation pattern already applied to `orchestrator.py` and `repl.py` keeps the codebase's structural conventions consistent.

## Implementation Intent
Extract each concern into its own module, following the constructor-injection / delegation pattern already used for the `orchestrator.py` split. Suggested (not mandatory) grouping, left for the implementation planning phase to finalize:
- MCP service health checks
- Tool-definition validation
- Workflow schema/definition validation
- Routing-drift validation
- Security-defaults auditing — the largest split target; consider further decomposing `audit_security_defaults()`'s individual checks (auth_token, shell sandbox, git/github/cicd allowlists, `ProductionConfigValidator` call, GitHub write settings) into separate helper functions within that module.

Preserve every public function's signature, return type, and exception-raising conditions exactly as-is, and keep `agent.startup`'s existing `from agent.repl_health import (...)` import path working without modification.

## Target Files or Areas
- `scripts/agent/repl_health.py` — primary target
- `tests/agent/test_repl_health.py`, `tests/agent/test_repl_health_malformed.py` — to be reorganized alongside the split
- `scripts/agent/startup.py` — import site; must continue to work unchanged
- Documentation: Unknown — check `docs/00_index.md`'s task-scope mapping against whichever files actually change before editing any doc

## Required Changes
- Decompose `audit_security_defaults()` into independently testable check functions.
- Split the file's five concerns into separate modules under `scripts/agent/`.
- Preserve every existing public function's signature, return type, and exception behavior (`check_service_health`, `check_readiness`, `check_tool_definitions_runtime`, `check_workflow_definition`, `check_workflow_schema`, `check_routing_drift`, `check_routing_safety_tiers`, `audit_security_defaults`).
- Keep `agent/startup.py`'s existing import statement working — either via a thin `repl_health.py` facade re-exporting the split symbols, or by updating the import statement itself (implementer's choice, documented in the resulting plan).
- Reorganize `test_repl_health.py`/`test_repl_health_malformed.py` to mirror the new module boundaries.

## Constraints
- Do not change `audit_security_defaults()`'s warning/error/`RuntimeError` decision logic — behavior must be identical before and after the split.
- Do not change any existing log message string — operators or monitoring may depend on exact wording.
- Keep changes to `scripts/agent/startup.py` limited to import statements, if any change is needed there at all.

## Acceptance Criteria
- Each resulting module addresses exactly one of the five concerns listed above.
- `audit_security_defaults()`'s logic is decomposed into independently testable units rather than one 200+ line function.
- All pre-existing tests in `test_repl_health.py` and `test_repl_health_malformed.py` (reorganized as needed) pass unchanged in outcome.
- `from agent.repl_health import (...)` in `scripts/agent/startup.py` continues to work without modification, or the import statement is updated and verified working.
- `ruff`, `mypy`, and `bandit` are clean on all new/modified files.
- A full `uv run pytest` run shows no new failures compared to the pre-change baseline.

## Testing Expectations
- Run the existing `test_repl_health.py` and `test_repl_health_malformed.py` suites (reorganized to match the new module layout) and confirm no behavioral regression.
- Run the full `uv run pytest` suite once after implementation and compare against the pre-change baseline for new failures.
- Apply the standard validation sequence in `rules/toolchain.md` (format → lint → type → arch → security → test → coverage).

## Documentation Impact
Unknown whether any `docs/*.md` file names these functions or file paths directly — check `docs/00_index.md`'s "Document References by Task" table against whichever files this issue's implementation actually touches, and update only the matched row(s). Do not proactively write new documentation beyond what routing directs.

## Out of Scope
- Changing any security check's pass/fail threshold or fail-open/fail-closed behavior.
- Adding new health-check or security-audit checks.
- Changing `scripts/agent/startup.py`'s logic beyond its import statement.
- Changing any log message or error message wording.
- Performance optimization of the health-check or audit code paths.

## Dependencies
N/A: none

## Unresolved Questions
- Exact module names and file layout for the five extracted concerns are left to the `issue-to-plan` / `plan-to-implementation-procedure` phases.
- Whether `agent/startup.py` should import directly from the new split modules, or `repl_health.py` should remain as a backward-compatible facade re-exporting them, is left to the implementer — document the choice in the resulting plan.

## AI Implementation Instruction
- Do not change observable behavior: preserve every public function's signature, return type, log message text, and exception-raising condition exactly.
- Extract `audit_security_defaults()` and the other four concerns into separate modules; you may follow the composition/delegation pattern used in `scripts/agent/orchestrator.py`'s split as a reference, but it is not mandatory.
- Verify `scripts/agent/startup.py`'s existing `from agent.repl_health import (...)` statement still works after the change (either unchanged or updated and confirmed working).
- Do not touch out-of-scope items (check thresholds, new checks, log wording, `startup.py` logic beyond imports).
- If a required design decision (module layout, facade vs. direct import) is unclear, stop and record it under Unresolved Questions rather than guessing.
