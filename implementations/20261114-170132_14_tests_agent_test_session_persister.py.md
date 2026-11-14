## Goal

Update `tests/agent/test_session_persister.py` so every `DiagnosticStore()` construction injects a validated `DiagnosticsConfig` snapshot and the patch of the deleted `_load_diagnostics_config` is dropped (`REQ-001`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `DiagnosticsConfig` (`config_dataclasses.py`) has three defaulted fields (`encryption_key=""`, `retention_days=30`, `sensitive_fields=frozenset(...)`); `DiagnosticsConfig()` yields the no-key configuration these tests exercise.
- `__post_init__` validation (`config_dataclasses.py` row) accepts the default instance, so constructing `DiagnosticsConfig()` in a test cannot raise.
- `SessionPersister` receives the store as a constructor argument, so injecting the config at `DiagnosticStore()` construction is where the wiring happens.

## Design decisions
- **Inject `DiagnosticsConfig()` at each `DiagnosticStore()` site.** Keeps each test's store keyed to the no-key path (`encryption_key=""`) the fixtures already assumed via the old `_load_diagnostics_config` mock.

## Alternatives considered
- **Keep mocking `_load_diagnostics_config`.** Rejected: `REQ-001` deletes that method; `patch.object(DiagnosticStore, "_load_diagnostics_config", ...)` would raise `AttributeError` once it is gone.

## Implementation
### Target file
`tests/agent/test_session_persister.py`
### Procedure
- Inject a validated `DiagnosticsConfig` into every `DiagnosticStore()` construction and remove the obsolete `_load_diagnostics_config` patch.
### Method
1. Add the import (next to line 17's `from agent.diagnostic_store import DiagnosticStore`):
   ```python
   +from agent.config_dataclasses import DiagnosticsConfig
   ```
2. Drop the `_load_diagnostics_config` patch from the `db` fixture (the `patch.object(...)` block at lines 71-77). The fixture keeps patching `agent.diagnostic_store.SQLiteHelper`; the store now reads the injected config instead of calling the removed method.
3. Inject `DiagnosticsConfig()` at every construction site. Each changes `DiagnosticStore()` → `DiagnosticStore(DiagnosticsConfig())`:
   - Line 101: `SessionPersister(_ctx(None), DiagnosticStore(), view)`
   - Line 112: `SessionPersister(_ctx(1), DiagnosticStore(), MagicMock())`
   - Line 121: `SessionPersister(_ctx(None), DiagnosticStore(), MagicMock())`
   - Line 125: `DiagnosticStore().save(None, kind="session_summary", content="{}")`
   - Line 136: `SessionPersister(ctx, DiagnosticStore(), view)`
   - Line 146: `store = DiagnosticStore()`
   - Line 172: `_ctx(db_session_id), DiagnosticStore(), MagicMock()`
   - Line 256: `SessionPersister(ctx, DiagnosticStore(), MagicMock())`
   - Line 275: `SessionPersister(ctx, DiagnosticStore(), MagicMock())`
### Details
- After removing the fixture's `_load_diagnostics_config` patch, NO remaining code in the file references that method (verified: only lines 17 and 72-73 did).
- `DiagnosticsConfig()` matches the old mock's no-key behavior (`encryption_key=""`), so the redaction/secret-check path these tests exercise is unchanged.

### Companion test files
N/A.

## Compatibility considerations
Every `DiagnosticStore()` call in this file must inject a config; any missed site raises `TypeError` (missing required `diagnostics_cfg`) at collection/run time.

## Security considerations
The store now runs with an explicit validated config rather than a mocked per-op read, so the no-key fail-closed path (`REQ-004`) is exercised against a real config instance.

## Rollback considerations
Revert the commit.

## Validation plan
- Unit: run the full `tests/agent/test_session_persister.py`; all gate/containment tests pass with the injected config and no `_load_diagnostics_config` reference remaining.
- Command: `uv run pytest tests/agent/test_session_persister.py`.

## Completion criteria
- No `DiagnosticStore()` construction in the file lacks `diagnostics_cfg`.
- No reference to `_load_diagnostics_config` remains.
- `test_session_persister.py` passes.

## Out of Scope
- Other test files' `DiagnosticStore()` constructions (`test_regression_diagnostic_persist.py`, its own row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Inject `DiagnosticsConfig()` at all 9 sites; drop the fixture patch |
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
- **Related target files**: `tests/agent/test_session_persister.py`
