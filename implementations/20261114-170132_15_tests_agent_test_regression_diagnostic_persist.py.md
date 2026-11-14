## Goal

Update `tests/agent/test_regression_diagnostic_persist.py` so every `DiagnosticStore(session_id=...)` construction injects a validated `DiagnosticsConfig` snapshot (`REQ-001`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `DiagnosticsConfig` (`config_dataclasses.py`) has three defaulted fields; `DiagnosticsConfig()` yields the no-key configuration these tests exercise (`encryption_key=""`).
- `__post_init__` validation accepts the default instance, so constructing `DiagnosticsConfig()` cannot raise.
- `diagnostics_cfg` is a required constructor parameter (Row 1); these callers already pass `session_id=` as a keyword, so inject `diagnostics_cfg=` as a keyword alongside it.

## Design decisions
- **Append `diagnostics_cfg=DiagnosticsConfig()` to each existing `session_id=` call.** Minimal, localized change; keeps each store on the no-key path the tests assume.

## Alternatives considered
- **Mock `_load_diagnostics_config`.** Rejected: `REQ-001` deletes that method; the store must receive the config at construction.

## Implementation
### Target file
`tests/agent/test_regression_diagnostic_persist.py`
### Procedure
- Inject a validated `DiagnosticsConfig` into every `DiagnosticStore(session_id=...)` construction.
### Method
1. Add the import (next to line 17's `from agent.diagnostic_store import DiagnosticStore`):
   ```python
   +from agent.config_dataclasses import DiagnosticsConfig
   ```
2. Inject `diagnostics_cfg=DiagnosticsConfig()` at each site (all use `session_id=` keyword):
   - Line 79: `store = DiagnosticStore(session_id=1)`
   - Line 91: `store = DiagnosticStore(session_id=1)`
   - Line 104: `store1 = DiagnosticStore(session_id=1)`
   - Line 105: `store2 = DiagnosticStore(session_id=2)`
   - Line 117: `store = DiagnosticStore(session_id=None)`
   Each becomes e.g. `DiagnosticStore(session_id=1, diagnostics_cfg=DiagnosticsConfig())`.
### Details
- The tests patch `agent.diagnostic_store.SQLiteHelper` and call `save()`/`fetch()`; `save()` now reads the injected config (no per-op read). `DiagnosticsConfig()` matches the prior no-key behavior, so the plain-string contents ("session 1 entry", "conn error") filter and secret-check identically.

### Companion test files
N/A.

## Compatibility considerations
Every `DiagnosticStore(...)` call in this file must pass `diagnostics_cfg`; any missed site raises `TypeError` (missing required argument) at run time.

## Security considerations
The store runs with an explicit validated config under the no-key fail-closed path (`REQ-004`) rather than a per-op config read.

## Rollback considerations
Revert the commit.

## Validation plan
- Unit: run the full `tests/agent/test_regression_diagnostic_persist.py`; cross-session isolation and null-session tests pass with the injected config.
- Command: `uv run pytest tests/agent/test_regression_diagnostic_persist.py`.

## Completion criteria
- No `DiagnosticStore(...)` construction in the file lacks `diagnostics_cfg`.
- `test_regression_diagnostic_persist.py` passes.

## Out of Scope
- Other test files' `DiagnosticStore()` constructions (`test_session_persister.py`, its own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Inject `diagnostics_cfg=DiagnosticsConfig()` at all 5 sites |
| 2 | Add or update tests per Validation plan | Pending | — | — | No new tests; existing tests updated in place |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001`
- **Source issue**: `issues/20261111-163701_diagstore002_diagnostic-store-fail-closed.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261114-161816_diagstore002_diagnostic-store-fail-closed.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261114-170132
- **Related target files**: `tests/agent/test_regression_diagnostic_persist.py`
