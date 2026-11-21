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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: same - affected tests only, no assertion changes proven |
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
- **Requirement ID**: REQ-003, REQ-004 (the self-resolved extension path becomes caller-supplied)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/db/recovery_verification.py`
