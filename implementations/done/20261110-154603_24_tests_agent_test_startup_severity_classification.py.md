## Goal
Drop the non-strict (WARNING) severity cases and strict toggles from `tests/agent/test_startup_severity_classification.py` because routing drift and tool-definition mismatch are always FATAL (`REQ-001`).

## Scope
**Release unit**: strict-only-startup


## Assumptions
- `_make_startup_ctx(tool_definitions_strict=...)` (line 29-39) sets `ctx.cfg.mcp.security_profile` and `ctx.cfg.tool.tool_definitions_strict`; both attributes leave the config. Plan wording gap (no extra file): this row's Plan text says "strict toggles" and cites REQ-001, but the file also uses `security_profile`/`SecurityProfile`, which `AC-07` requires to be absent from `tests/`; the same edit removes them. No additional target file is involved.

## Design decisions
- Keep the FATAL assertions (they now describe the only behavior), rename tests that say "strict"/"regardless of strict", delete tests whose only claim is the WARNING path.

## Alternatives considered
N/A: the WARNING path no longer exists.

## Implementation
### Target file
`tests/agent/test_startup_severity_classification.py`

### Procedure
- Remove the `SecurityProfile` import (line 26), the `tool_definitions_strict` parameter, and the two attribute assignments in `_make_startup_ctx()`.
- `test_routing_drift_unexpected_failure_is_fatal_when_strict` (line 322): drop the `routing_drift_strict = True` line and rename to `test_routing_drift_unexpected_failure_is_fatal` (new); update its docstring.
- Delete `test_routing_drift_unexpected_failure_is_warning_when_not_strict` (line ~335) and `test_routing_drift_unreadable_strictness_is_fatal` (line ~364, no setting left to read).
- `test_routing_drift_runtime_error_is_fatal_regardless_of_strict` (line ~349): drop the `routing_drift_strict = False` line and rename to `test_routing_drift_runtime_error_is_fatal` (new).
- `test_routing_safety_tiers_unexpected_failure_is_fatal` (line ~403): drop the `routing_drift_strict = False` line and the "whatever the drift policy" clause.
- Delete `test_routing_drift_live_warning_when_non_strict_drift` (line ~436); in `test_routing_drift_live_skipped_on_exception` (line ~460) call `_make_startup_ctx()` without the argument.

### Method
- Use `rg -n 'strict|WARNING' tests/agent/test_startup_severity_classification.py` after editing to confirm no non-strict case is left.

### Details
- Related duplicated cases live in `tests/agent/test_startup.py` and `tests/agent/test_startup_memory_failures.py` (own documents); do not touch them here.

## Compatibility considerations
Test-only; depends on `startup_validation.py` and `mcp_tool_discovery.py` documents (release unit).

## Security considerations
Keeps every FATAL assertion; only WARNING-path cases for a removed mode are deleted.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run pytest tests/agent/test_startup_severity_classification.py -v`
- `uv run ruff format` and `uv run ruff check` on the file
- `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`
- `uv run pytest tests/agent tests/shared tests/integration -v` (full Phase 5 pass once every document is implemented)

## Completion criteria
- No `tool_definitions_strict`, `routing_drift_strict`, or `SecurityProfile` remains; no test asserts WARNING for drift; the file passes (`AC-01`, `AC-07`).

## Out of Scope
- Source edits; other startup test files.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the strict and profile attributes from the helper and rename or delete the strict/non-strict cases | Done | 20261110-172551 | 20261110-172551 | renamed 3 tests, deleted 3 WARNING/strictness tests; rg clean |
| 2 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 20261110-172551 | — | file-level ruff + `pytest -v`: 24 passed; mypy deferred to the code-batch end gate |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001` (non-strict severity cases are dropped; drift is always FATAL)
- **Source issue**: issues/20261109-112640_adrrev004_non-strict-bypass-removal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-094140_adrrev004_non-strict-bypass-removal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-154603
- **Related target files**: `tests/agent/test_startup_severity_classification.py`
