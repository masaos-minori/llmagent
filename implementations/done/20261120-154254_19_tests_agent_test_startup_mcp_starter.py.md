## Goal

Remove every `check_routing_drift()` reference from `tests/agent/test_startup_mcp_starter.py` (`REQ-004`, scope approved). `check_routing_drift()` is removed by row 16 (`routing_drift.py`); this file imports it (line 7) and exercises it in five routing-drift tests. Once removed, the import raises `ImportError` and every call/site breaks. Keep the file's other suites (post-startup health verification, lifecycle router) untouched.

## Scope
**Release unit**: static-catalog removal

## Assumptions
- Current source has FIVE `check_routing_drift` tests (the Plan's Evidence cited only two): `test_routing_drift_non_strict_returns_warnings` (L32), `test_routing_drift_strict_raises` (L43), `test_routing_drift_no_drift_returns_empty` (L52), `test_routing_drift_unexpected_error_propagates_when_non_strict` (L61), `test_routing_drift_unexpected_error_propagates_when_strict` (L71). All call `check_routing_drift(...)`; the last two also patch `shared.tool_routing_validation.validate_routing_against_config`.
- After removing those five tests, the following become unused and must go too:
  - `from agent.services.routing_drift import check_routing_drift` (line 7).
  - `_make_ctx()` helper (lines 15-22) — used only by the five tests.
  - `ToolDefinition` and `get_registry` from the `shared.tool_registry` import (lines 9, 11) — used only by the five tests.
- `MagicMock`, `patch`, and `_reset_registry_for_testing` are still used by the surviving suites (health verification uses `MagicMock`; `setup_function` uses `_reset_registry_for_testing`; later tests use `patch`), so their imports stay.
- The module docstring ("Tests for routing drift strict mode checks") describes removed behavior; update it to match the remaining health-verification scope.

## Design decisions
- Delete the five `check_routing_drift` test functions and their `# --- check_routing_drift strict mode ---` section header.
- Drop the `check_routing_drift` import and collapse the `shared.tool_registry` import to `_reset_registry_for_testing` only.
- Delete the `_make_ctx` helper.
- Reword the module docstring to reflect the remaining scope (health verification), removing the "routing drift strict mode" claim.

## Alternatives considered
- Keeping the tests behind a skip marker: rejected because they call a function that no longer exists; a skipped import error cannot be skipped.
- Rewriting the tests against `validate_routing_against_live()`: rejected because these tests specifically exercise `check_routing_drift`'s strict/non-strict error propagation, which has no live equivalent; the live path is covered elsewhere.

## Implementation
### Target file
`tests/agent/test_startup_mcp_starter.py`

### Procedure
Remove the `check_routing_drift` import, the `_make_ctx` helper, and the five routing-drift tests; update the module docstring.

### Method
1. Replace the top-of-file import block:
   ```python
   from agent.services.routing_drift import check_routing_drift
   from shared.tool_registry import (
       ToolDefinition,
       _reset_registry_for_testing,
       get_registry,
   )
   ```
   with
   ```python
   from shared.tool_registry import _reset_registry_for_testing
   ```
2. Delete the `_make_ctx` helper (lines 15-22) and its trailing blank lines, leaving `setup_function` directly after the imports.
3. Delete the `# --- check_routing_drift strict mode ---` section header and the five routing-drift test functions it introduces, leaving the `# --- post-startup health verification ...` section intact.
4. Change the module docstring (line 1) from `"Tests for routing drift strict mode checks."` to something matching the remaining scope, e.g. `"Tests for MCP server startup health verification."`.

### Details
- Confirm no `check_routing_drift`, `ToolDefinition`, `get_registry`, or `_make_ctx` reference remains anywhere in the file.
- Confirm `MagicMock`, `patch`, and `_reset_registry_for_testing` are still referenced (they are) so their imports resolve.
- Do not touch any health-verification or lifecycle-router test (lines 82+).

## Compatibility considerations
Test-only change. Removes dead tests for a removed function; the surviving suites are unchanged. No production compatibility impact.

## Security considerations
N/A: test-only. Removing tests for the config-based `check_routing_drift` (a weaker drift path) loses no fail-closed coverage — live-vs-registry drift detection remains via `validate_routing_against_live()` (row 8).

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Run `pytest tests/agent/test_startup_mcp_starter.py` and assert the full suite collects and passes (no import error, no missing-symbol errors).
- Confirm the five routing-drift tests are gone and the health-verification/lifecycle tests remain.
- Run ruff on the file to confirm no unused-import (`F401`) warnings remain after the import collapse.

## Completion criteria
`test_startup_mcp_starter.py` contains no `check_routing_drift` / `ToolDefinition` / `get_registry` / `_make_ctx` reference; the module imports cleanly; the remaining health-verification suite passes.

## Out of Scope
The `check_routing_drift()` removal (`routing_drift.py`, row 16), the `startup_validation.py` call-site/import removal (row 17), the `validate_routing_against_config()` removal (`tool_routing_validation.py`, row 8), and the cascade fixes to the non-Plan startup test files (rows 23-27).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261120 | 20261120 | Deleted the module docstring ("Tests for routing drift strict mode checks." → "Tests for MCP server startup health verification."), collapsed the top import block to `from shared.tool_registry import _reset_registry_for_testing`, deleted the `_make_ctx` helper, and removed the `# --- check_routing_drift strict mode ---` section plus its five test functions. No `check_routing_drift`/`ToolDefinition`/`get_registry`/`_make_ctx`/`validate_routing_against_config` reference remains; `MagicMock`/`patch`/`_reset_registry_for_testing` still used (40 refs). |
| 2 | Add or update tests per Validation plan | N/A | — | — | Removes existing dead tests; no new tests required. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261120 | 20261120 | ruff format/check clean; target suite `tests/agent/test_startup_mcp_starter.py` collects and passes (15 passed, 5 routing-drift tests gone, health-verification/lifecycle suites intact). Full-suite regression diff DEFERRED to the `_16`–`_27` coupled-unit final check. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Test-only; module docstring updated to reflect remaining scope. |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: `issues/20261120-114210_agentcfg002_tool-catalog-registry.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-151418_agentcfg002_tool-catalog-registry.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-154254
- **Related target files**: `tests/agent/test_startup_mcp_starter.py`
