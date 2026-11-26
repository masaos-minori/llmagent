## Goal

Derive per-server post-shutdown state from termination outcomes, reject invalid transitions without mutating state, and raise typed suppression errors from `ensure_ready()`/`restart()` during shutdown (REQ-006, REQ-007, REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 2 is outside R3-ownership; the Phase 4 part of this row lands with R3-ownership)

## Assumptions
- The error family is declared by row 08 (`scripts/agent/http_lifecycle_errors.py`); `StartSuppressedError` stays in this file at `:45` because `scripts/agent/startup_mcp_starter.py:23` imports it from here (Plan Assumptions).
- New states come from row 01's extended `LifecycleState`.

## Design decisions
- `_set_state` rejects by logging and leaving the state unchanged, not by raising: a raise would propagate into `shutdown_all`'s per-server loop and turn a reporting step into a failure path (Plan Design).
- Suppression errors are `RuntimeError` subclasses, so the two known callers (`scripts/shared/tool_transport_invoker.py:282`, `startup_mcp_starter.py:188`) handle them unchanged.

## Alternatives considered
- Raising from `_set_state` — rejected per Plan Design (observability via log + unchanged state is what AC-3 tests).

## Implementation
### Target file
`scripts/agent/lifecycle_router.py`

### Procedure
- `_set_state` (`:174`): on `assert_valid_transition` failure, log and return without the assignment at `:196`.
- `shutdown_all` (`:275`): replace the global `STOPPED` loop (`:281-282`) with per-server states from the returned outcomes (`STOPPED` confirmed, `EXIT_UNCONFIRMED`, `SIGNAL_NOT_DELIVERED`).
- `ensure_ready` (`:238`, silent return at `:240-244`) and `restart` (`:312`, silent return at `:314-318`): raise `EnsureSuppressedError` (new) / `RestartSuppressedError` (new) after the existing log.
- `start_http_subprocess` (`:114`): rewire the `_http_mgr._http_procs.get(server_key)` return (`:121`, verified 2026-11-26) to the record registry — return `record.process` from `_records`, or None when no record exists (row 03 removed the dicts).

### Method
Three localized changes in the router; the state mapping reads the coordinator's per-server outcomes (row 04) through the record (row 02).

### Details
- Keep the existing warning/debug log lines; the raise replaces only the `return`.
- Restart refusal from the manager (`RestartBlockedError` (new)) maps to `EXIT_UNCONFIRMED` (new) and cooldown handling unchanged (Plan Design).

### Companion test files
- `tests/agent/test_agent_factory.py`
  - Procedure: update `TestRouterInvalidTransitionLogging` (`:743-751`) from asserting the mutate-after-warning behavior to asserting no mutation (REQ-011, Phase 1).
  - Validation: `uv run pytest tests/agent/test_agent_factory.py`.

## Compatibility considerations
- Callers that never expected an exception from `ensure_ready`/`restart` during shutdown: the two known callers already handle the `RuntimeError` family (Plan Risks); impact-radius grep over callers precedes Phase 4.

## Security considerations
- N/A.

## Rollback considerations
- Revert the commit.

## Validation plan
- Unit: no-mutation and suppression tests — `uv run pytest tests/agent/test_lifecycle.py tests/agent/test_agent_factory.py` (AC-3, AC-4).

## Completion criteria
- An invalid transition leaves the state unchanged and logs; every shutdown-time `ensure_ready`/`restart` call raises a typed error; post-shutdown states are per-server, not global (AC-3, AC-4, AC-5).

## Out of Scope
- The transition table itself (row 01), the error class definitions (row 08), the protocol docstrings (row 07).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261126-134500 | 20261126-140500 | Changed files: scripts/agent/lifecycle_router.py; scripts/agent/lifecycle.py (verification correction: STARTING -> EXIT_UNCONFIRMED/SIGNAL_NOT_DELIVERED added to _VALID_TRANSITIONS, required by the restart-refusal mapping in this row's Details; recorded in row 01 Notes too); tests/agent/test_startup_mcp_starter.py (fallout fix: _real_router_ctx retargeted to _records because this row rewires start_http_subprocess) |
| 2 | Add or update tests per Validation plan | Completed | 20261126-140500 | 20261126-141000 | Companion row 16; test_lifecycle.py is its own row (11) Companion row 16: tests/agent/test_agent_factory.py updated - TestRouterInvalidTransitionLogging asserts no mutation (STOPPED->STOPPING stays STOPPED); shutdown-guard tests assert EnsureSuppressedError/RestartSuppressedError; fixtures retargeted to _records with shutdown_all return_value=[]; 57 passed; test_startup_mcp_starter.py 16 passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-141100 | 20261126-133051 | Fast gates pass (ruff/format/mypy/lint-imports/bandit -ll/check_module_size/check_docstrings). Allowed red (Failure Log, unchanged set): dict-pinned tests test_http_lifecycle.py (row 12), test_http_lifecycle_integration.py (row 14), test_lifecycle.py (row 11), test_startup_mcp_lifecycle.py (amended 22), test_http_lifecycle_warning.py (amended 23). Full-suite run at end of batch End-of-batch full-suite run: 15103 passed, 5 skipped; coverage xml + diff-cover --compare-branch=master --fail-under=90: 93% (99 new lines, 6 missing). Allowed-red set fully retired |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | Docs rows 19-23 N/A: docs covered by rows 19-23 |

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
- **Requirement ID**: REQ-006 (per-server states), REQ-007 (no mutation on invalid transition), REQ-008 (typed suppression errors)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `scripts/agent/lifecycle_router.py`, `tests/agent/test_agent_factory.py`