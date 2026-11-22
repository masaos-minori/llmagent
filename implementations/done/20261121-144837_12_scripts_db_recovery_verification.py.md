## Goal

Stop `scripts/db/recovery_verification.py` from resolving `sqlite_vec_so` through its own `agent.toml` load; use the injected typed configuration (REQ-003, REQ-004, AC-004).

## Scope
**Release unit**: RU-2

## Assumptions
- `tests/db/test_db_recovery.py` and `tests/db/test_schema_validation_per_database.py` are run as affected tests and are not target rows; the patch targets remain valid through Design D3.
- The fail-closed behaviour for a configuration that cannot supply `sqlite_vec_so` is preserved.

## Design decisions
- The function that verifies a database receives the typed configuration from its caller instead of constructing it; the fail-closed `verification_unavailable` return is kept.

## Alternatives considered
- N/A: single call-site change.

## Implementation
### Target file
`scripts/db/recovery_verification.py`
### Procedure
- Update the `build_db_config()` call (line 151) to the injected-configuration signature defined by Plan row 8.
- Update the docstring paragraph that says the extension path is resolved here (line 136) to say it is supplied by the caller.
### Method
- No change to the verification logic or to the `SQLiteHelper` construction.
### Details
- Verified 2026-11-21: `tests/db/test_schema_validation_per_database.py` patches `db.helper.build_db_config`, not this module's call; that test is unaffected by the name, only by the signature, which is covered by Plan row 25's test-document work.
- Finding (2026-11-21, execution): with the typed configuration as an argument the `except ValueError` branch cannot be reached, so it was removed; the fail-closed behaviour it produced now belongs to the caller that constructs the typed configuration. `tests/db/test_db_recovery.py` (the "config cannot supply sqlite_vec_so" case, patching `db.recovery_verification.build_db_config`) must assert the caller-side rejection instead — recorded as an affected-test change.
- Finding (2026-11-21, execution): the signature is `_run_logical_verification(db_config, db_path, target)`, which also changes the two call sites in `scripts/db/recovery.py` (Plan row 11).
- Finding (2026-11-22, execution): the earlier repair pass had re-inserted the pre-change test `test_logical_verification_config_failure_is_verification_unavailable`, which patches `db.recovery_verification.build_db_config` — a name this module no longer imports — alongside the caller-side assertion test. The stale duplicate was removed; the caller-side test (`test_logical_verification_config_failure_is_rejected_by_the_owner`) is the surviving evidence. `tests/db/test_db_recovery.py` is green (93 passed).

## Compatibility considerations
- The `except ValueError` path that logs and returns `verification_unavailable` stays; with injection the caller raises earlier, so the behaviour for the same values is unchanged.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py tests/db/test_schema_validation_per_database.py -v` (affected tests)
- `uv run python tools/check_db_separation.py`, `uv run python tools/check_mock_patch_targets.py`
- `uv run ruff check scripts/db/recovery_verification.py`, `uv run mypy scripts/db/recovery_verification.py`

## Completion criteria
- No `ConfigLoader` use in this module; the same configured `sqlite_vec_so` value produces the same verification result.

## Out of Scope
- Definition of the typed configuration (Plan row 9), the caller-side construction (Plan row 16), test changes (Plan row 25).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-22 | 2026-11-22 | Implemented under the gate. Finding: Plan Design D3's claim that patch targets for db.*.build_db_config stay valid is invalid here, because this module takes the typed configuration. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | Affected tests only; the helper builds DbConfig directly (tests/db/test_schema_validation_per_database.py::_entry_workflow) and the file is green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | $V |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Documentation landed with Plan row 30. |

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
- **Requirement ID**: REQ-003, REQ-004 (the self-resolved extension path becomes caller-supplied)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/db/recovery_verification.py`
