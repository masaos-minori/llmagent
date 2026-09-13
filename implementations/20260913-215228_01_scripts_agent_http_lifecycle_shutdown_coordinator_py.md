## Goal

Eliminate the duplicate `_absorb_sigint_during_shutdown` implementation between `HttpServerLifecycleManager` (`http_lifecycle.py`) and `ShutdownCoordinator` (`http_lifecycle_shutdown_coordinator.py`) by extracting it to a single module-level function in `http_lifecycle_shutdown_coordinator.py`, per REQ-001 and REQ-002.

## Scope

- In-Scope: Extracting `_absorb_sigint_during_shutdown`'s body to one module-level function; making both `HttpServerLifecycleManager` and `ShutdownCoordinator`'s existing `_absorb_sigint_during_shutdown` attribute an alias (`staticmethod`) to that shared function, so `manager._absorb_sigint_during_shutdown` and `ShutdownCoordinator._absorb_sigint_during_shutdown` continue to exist and resolve to the same underlying function
- Out-of-Scope: Consolidating the two classes' actual shutdown *logic* (`HttpServerLifecycleManager.shutdown_all()`'s `_terminate_with_timeout`-based per-process termination vs. `ShutdownCoordinator.shutdown_all()`'s SIGTERM→timeout→SIGKILL process-group escalation); removing `ShutdownCoordinator.shutdown_all()` as dead code (a separate cleanup, not part of this fix); changing the SIGTERM→SIGKILL escalation timing; any change to `HttpServerLifecycleManager`'s public API surface

## Assumptions

- No caller depends on `HttpServerLifecycleManager._absorb_sigint_during_shutdown` and `ShutdownCoordinator._absorb_sigint_during_shutdown` being *different* function objects (e.g. for per-class log-message differentiation) — none found in this cycle's search of `scripts/` and `tests/`
- `ShutdownCoordinator.shutdown_all()` remaining unreachable in production is acceptable for this Plan's scope — its removal (or wiring it up) is a separate, larger decision (see Unknowns)

## Design decisions

1. Use a `staticmethod` alias (`ClassName._absorb_sigint_during_shutdown = staticmethod(shared_func)`) rather than simply deleting one class's method and redirecting call sites to import the module-level function directly — this preserves `hasattr(HttpServerLifecycleManager, "_absorb_sigint_during_shutdown")` and the identity-check assertion in `test_shutdown_all_installs_guard_handler` without modifying any existing test
2. Place the shared module-level function in `http_lifecycle_shutdown_coordinator.py` (not `http_lifecycle_errors.py`, which the Issue's Implementation Intent also suggested) — `http_lifecycle_errors.py`'s stated purpose is "Exceptions and dataclasses for HTTP subprocess MCP server startup failures," semantically unrelated to a shutdown signal handler; `http_lifecycle_shutdown_coordinator.py` already hosts semantically related module-level helpers (`_get_pgid`, `_kill_pg`, `_kill_pg_force`) and `http_lifecycle.py` already imports from it, so no new import edge or circular-import risk is introduced
3. Do not consolidate the two `shutdown_all()` termination-logic implementations — that is a separate, larger concern tracked as UNK-01, which this Plan's narrower scope (matching the Issue's literal title) does not require

Evidence grounding:
- Both `_absorb_sigint_during_shutdown` methods are identical `@staticmethod`s (same body, same log message `"Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes"`), each installed via `signal.signal(signal.SIGINT, ...)` inside their own class's `shutdown_all()`
- Re-verified 2026-09-13: `ShutdownCoordinator.shutdown_all()` is unreachable dead code — only `HttpServerLifecycleManager.shutdown_all()` is invoked in production code (`factory.py:171`)
- Existing tests directly assert on `HttpServerLifecycleManager._absorb_sigint_during_shutdown`'s identity and presence: `test_absorb_sigint_handler_exists` (`hasattr` check, line 49; monkeypatches the attribute via `patch.object`, lines 55-58) and `test_shutdown_all_installs_guard_handler` (line 89: `assert installed_handler is manager._absorb_sigint_during_shutdown` — an identity check, not just an equality check)

## Alternatives considered

- **Delete one class's method and redirect call sites**: Rejected because it would modify existing test assertions (identity checks, `hasattr` checks) and requires changing all call sites. The `staticmethod` alias approach preserves backward compatibility without touching tests.
- **Move to `http_lifecycle_errors.py`**: Rejected because that module's stated purpose is "Exceptions and dataclasses for HTTP subprocess MCP server startup failures," semantically unrelated to a shutdown signal handler. `http_lifecycle_shutdown_coordinator.py` already hosts semantically related module-level helpers.
- **Consolidate both `shutdown_all()` implementations**: Rejected because it would silently switch production behavior to the currently-unused, untested code path — a materially larger and riskier change than what the Issue's title describes. Tracked as UNK-01 for a separate decision.

## Implementation
### Target files
- `scripts/agent/http_lifecycle_shutdown_coordinator.py`
- `scripts/agent/http_lifecycle.py`

### Procedure
1. Confirm the alias preserves all existing test assertions
2. Add module-level `_absorb_sigint_during_shutdown()` function to `http_lifecycle_shutdown_coordinator.py`
3. Replace `ShutdownCoordinator._absorb_sigint_during_shutdown` with a `staticmethod` alias
4. Import the module-level function in `http_lifecycle.py` and replace `HttpServerLifecycleManager._absorb_sigint_during_shutdown` with the same `staticmethod` alias
5. Update both classes' `shutdown_all()` docstrings to note the shared handler
6. Run validation sequence

### Method
Module-level function extraction + `staticmethod` alias replacement in both classes.

### Details
1. **Phase 1: Preparation — Confirm the alias preserves all existing test assertions**
   a. Re-read `tests/agent/test_http_lifecycle_integration.py::TestSignalHandling`'s 4 tests in full to confirm the `staticmethod` alias approach satisfies each one's assertion pattern (`hasattr`, `patch.object`, `is` identity, log message substring) without modification
   
2. **Phase 2: Core Logic — Extract and alias**
   a. Locate the existing module-level helpers in `http_lifecycle_shutdown_coordinator.py` (lines 25-49: `_get_pgid`, `_kill_pg`, `_kill_pg_force`) — these establish the module-level-function pattern this follows
   
   b. Add module-level `_absorb_sigint_during_shutdown(signum: int, frame: object) -> None` function alongside them:
      ```python
      def _absorb_sigint_during_shutdown(signum: int, frame: object) -> None:
          """Absorb SIGINT signals during shutdown_all() cleanup."""
          logger.warning("Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes")
      ```
   
   c. Replace `ShutdownCoordinator._absorb_sigint_during_shutdown`'s method body (lines 55-60):
      ```python
      # Before:
      @staticmethod
      def _absorb_sigint_during_shutdown(signum: int, frame: object) -> None:
          logger.warning("Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes")
      
      # After:
      _absorb_sigint_during_shutdown = staticmethod(_absorb_sigint_during_shutdown)
      ```
   
   d. In `http_lifecycle.py`, import the module-level function:
      ```python
      # Add import at top of http_lifecycle.py:
      from .http_lifecycle_shutdown_coordinator import _absorb_sigint_during_shutdown
      ```
   
   e. Replace `HttpServerLifecycleManager._absorb_sigint_during_shutdown`'s method body (lines 528-538):
      ```python
      # Before:
      @staticmethod
      def _absorb_sigint_during_shutdown(signum: int, frame: object) -> None:
          logger.warning("Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes")
      
      # After:
      _absorb_sigint_during_shutdown = staticmethod(_absorb_sigint_during_shutdown)
      ```
   
   f. Update both classes' `shutdown_all()` docstrings to note the shared handler:
      - Add a note in `HttpServerLifecycleManager.shutdown_all()`'s docstring (line 541) explaining that the SIGINT-absorb handler is now a single shared function defined in `http_lifecycle_shutdown_coordinator.py`
      - Add a similar note in `ShutdownCoordinator.shutdown_all()`'s docstring (line 64)

3. **Phase 3: Deployment & Verification**
   a. Run `pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_lifecycle.py` to verify existing and new tests pass

## Compatibility considerations

- A `staticmethod` alias could behave subtly differently from a normal method under `patch.object()` monkeypatching (used by `test_absorb_sigint_handler_exists`) — mitigated by the fact that `staticmethod`-wrapped functions support `patch.object()` replacement identically to regular methods in Python's `unittest.mock`; this is standard, well-tested `unittest.mock` behavior
- Leaving `ShutdownCoordinator.shutdown_all()`'s termination logic un-consolidated could be read as "the fix is incomplete" against the Issue's Implementation Intent — mitigated by Background and Design explicitly documenting why full consolidation is out of scope (a materially larger, riskier change than the Issue's literal title describes) and tracking it as UNK-01 for a separate decision

## Security considerations

N/A: Refactoring only, no security impact.

## Rollback considerations

Simple revert of the three modifications (module-level function addition, two `staticmethod` alias replacements, two docstring updates) — no data migration or state rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/http_lifecycle_shutdown_coordinator.py | Unit — verify ShutdownCoordinator._absorb_sigint_during_shutdown resolves to the shared module-level function | New identity-check test | is comparison passes |
| scripts/agent/http_lifecycle.py | Integration — verify existing SIGINT install/restore behavior is unchanged | pytest tests/agent/test_http_lifecycle_integration.py -k Signal | All existing assertions pass unmodified |

## Completion criteria

- [ ] `HttpServerLifecycleManager._absorb_sigint_during_shutdown` and `ShutdownCoordinator._absorb_sigint_during_shutdown` are the identical function object (verified via `is`)
- [ ] The shared function's log message text is unchanged (`"Lifecycle: SIGINT received during shutdown_all(); ignoring until cleanup completes"`)
- [ ] `HttpServerLifecycleManager.shutdown_all()`'s SIGINT install/restore behavior is unchanged
- [ ] `ShutdownCoordinator.shutdown_all()`'s SIGINT install/restore behavior is unchanged
- [ ] All existing tests in `tests/agent/test_http_lifecycle_integration.py::TestSignalHandling` and the broader `shutdown_all`-related test suites pass without modification

## Out of scope

- Modifying `tests/agent/test_http_lifecycle_integration.py` (reference file only)
- Modifying `scripts/agent/factory.py` (reference file only)
- Consolidating the two `shutdown_all()` termination-logic implementations
- Removing `ShutdownCoordinator.shutdown_all()` as dead code
- Changing the SIGTERM→SIGKILL escalation timing
- Any change to `HttpServerLifecycleManager`'s public API surface

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm alias preserves test assertions | Pending | — | — | Read TestSignalHandling 4 tests |
| 2 | Add module-level _absorb_sigint_during_shutdown() function | Pending | — | — | Alongside _get_pgid/_kill_pg/_kill_pg_force |
| 3 | Replace ShutdownCoordinator._absorb_sigint_during_shutdown with staticmethod alias | Pending | — | — | Line 55-60 |
| 4 | Import shared function in http_lifecycle.py | Pending | — | — | from .http_lifecycle_shutdown_coordinator import |
| 5 | Replace HttpServerLifecycleManager._absorb_sigint_during_shutdown with staticmethod alias | Pending | — | — | Line 528-538 |
| 6 | Update HttpServerLifecycleManager.shutdown_all() docstring | Pending | — | — | Note shared handler |
| 7 | Update ShutdownCoordinator.shutdown_all() docstring | Pending | — | — | Note shared handler |
| 8 | Run pytest tests/agent/test_http_lifecycle_integration.py tests/agent/test_lifecycle.py | Pending | — | — | Verify existing and new tests pass |

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
- **Requirement ID**: REQ-001, REQ-002 — consolidate duplicate SIGINT-absorb handler between HttpServerLifecycleManager and ShutdownCoordinator
- **Source issue**: issues/20260913-171653_duplicate_sigint_handler.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-200656_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-215228
- **Related target files**: scripts/agent/http_lifecycle.py, scripts/agent/http_lifecycle_shutdown_coordinator.py
