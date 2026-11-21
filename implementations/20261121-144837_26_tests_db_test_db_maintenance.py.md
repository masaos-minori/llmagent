## Goal

Replace the `from_config()` and default-mode tests with tests that construct the typed maintenance configuration and inject it (REQ-004; AC-004, AC-005).

## Scope
**Release unit**: RU-2

## Assumptions
- This row is not a companion: `tests/db/test_db_maintenance.py` is named by three rows (`scripts/db/maintenance.py`, `scripts/db/rotation.py`, `scripts/db/artifact_retention.py`), so it keeps its own document.
- `tests/db/test_recovery_drill.py` is run as an affected test and is not a target row.
- The asserted behaviour itself does not change: the boundary semantics (negative/bool/float rejected, `0` disables a rule) stay, only how the values arrive changes.

## Design decisions
- Tests build the typed configuration directly and pass it to the dataclasses and to `checkpoint_wal()`; the `patch("db.maintenance.ConfigLoader")` fixtures disappear because the module no longer loads a file.
- The key-naming `ValueError` messages stay asserted, because the error text names the key the user writes and is part of the documented contract.

## Alternatives considered
- Keep the config-load tests as a thin wrapper over a supplied mapping: rejected — that keeps a dependency the row's responsibility removes.

## Implementation
### Target file
`tests/db/test_db_maintenance.py`
### Procedure
- Replace the `from_config()` calls (lines 1462-1487, 1612) with typed construction from a mapping, and keep the boundary matrix.
- Replace `test_checkpoint_wal_default_mode_from_config` (line 384) with a case that passes the typed configuration and asserts the mode it carries.
- Keep the patch targets for `build_db_config` valid through the preserved name (Plan row 8); update the arguments they pass.
### Method
- Direct construction plus injection; no new fixtures, no filesystem reads.
### Details
- Verified 2026-11-21: the file already constructs `RetentionConfig` and `CorruptArchiveRetentionConfig` directly in the boundary tests, so the change is limited to replacing the `from_config()` entry point; the active-session guard and the tie-breaking order tests are unaffected.

## Compatibility considerations
- `tests/db/test_db_maintenance.py` is the largest test file in this Plan; run the whole `tests/db/` suite so the shared fixture (Plan row 20) is exercised together.

## Security considerations
- N/A: test-only change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/db/test_db_maintenance.py tests/db/test_recovery_drill.py -v`
- `uv run pytest tests/db/ -v`
- `uv run python tools/check_mock_patch_targets.py`
- `uv run ruff check tests/db/test_db_maintenance.py`, `uv run mypy tests/db/test_db_maintenance.py`

## Completion criteria
- Every maintenance value in the tests arrives through the injected typed configuration; the boundary and tie-breaking assertions pass unchanged; no test patches `db.maintenance.ConfigLoader`.

## Out of Scope
- Definition of the typed configuration (Plan row 9), the caller-side construction (Plan row 16), documentation updates (Plan row 30).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: same - shared surface must be re-verified after that Issue lands |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | Gated: same - shared surface must be re-verified after that Issue lands |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Gated: same - the maintenance documentation row is Plan row 30 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|---|---|---|---|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-004 (injected typed maintenance configuration tests)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `tests/db/test_db_maintenance.py`
