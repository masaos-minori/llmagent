## Goal

Resolve recovery paths and the recovery policy through the injected typed configuration, with no `agent.toml` load inside `scripts/db/` and no database behaviour change (REQ-003, REQ-005, AC-004, AC-005).

## Scope
**Release unit**: RU-2

## Assumptions
- `tests/db/test_db_recovery.py` is run as an affected test and is not a target row; patch targets stay valid because `build_db_config()` keeps its name (the Plan's Design D3).
- Recovery policy alignment means only the configuration source changes; the recovery behaviour itself is preserved per the Issue's AI Implementation Instruction.

## Design decisions
- `recover_corruption()` receives the typed configuration from its caller instead of calling `build_db_config()` with no argument; the caller that owns `config/agent.toml` is the Agent side (Plan row 16) or the test fixture (Plan row 20).

## Alternatives considered
- N/A: the call-site change is the smallest change that satisfies AC-004 for this module.

## Implementation
### Target file
`scripts/db/recovery.py`
### Procedure
- Change the `build_db_config()` call (line 588) to the injected-configuration signature defined by Plan row 8.
- Document the owner/reader map for the paths this module resolves, per the Plan's Design D1.
### Method
- No change to the recovery or quarantine logic; the values arrive as an argument.
### Details
- Verified 2026-11-21: this module imports `build_db_config` from `db.config` and uses it for path resolution; the corrupt-archive policy is defined in `db/maintenance.py` (Plan row 9), not here.
- Finding (2026-11-21, execution): `build_db_config()` is no longer called here, so the row's assumption that `patch("db.recovery.build_db_config")` stays valid no longer holds; the tests in `tests/db/test_db_maintenance.py` and `tests/db/test_db_recovery.py` supply `DbConfig` directly. Recorded in Plan row 26.
- Finding (2026-11-21, execution): `db_config` is threaded through the internal helpers that reach the connection layer — `_vacuum_db()`, `_verify_candidate()`, `_post_restore_failure()`, `_result_for_condition()`, `_restore_from_backup()` — because `SQLiteHelper` and `_run_logical_verification()` take the typed configuration (Plan rows 12, 15). The procedure named only the `build_db_config()` call site.

## Compatibility considerations
- Config-load failures that previously propagated from this module now come from the caller; the documented BEST_EFFORT exception in `docs/41_db/db_06_api_and_operations-maintenance-and-rotation.md` is updated by Plan row 30.

## Security considerations
- N/A: no trust-boundary change.

## Rollback considerations
- N/A: revert the commit within release unit RU-2.

## Validation plan
- `uv run pytest tests/db/test_db_recovery.py -v` (affected test)
- `uv run pytest tests/integration/test_session_recovery.py -v`
- `uv run python tools/check_db_separation.py`, `uv run python tools/check_mock_patch_targets.py`
- `uv run ruff check scripts/db/recovery.py`, `uv run mypy scripts/db/recovery.py`

## Completion criteria
- No `ConfigLoader` use in this module; every path and policy value comes from the injected typed configuration; recovery behaviour is byte-for-byte unchanged for the same values.

## Out of Scope
- Definition of the typed maintenance configuration (Plan row 9), the caller-side construction (Plan row 16), documentation updates (Plan row 30).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|---|---|---|---|---|---|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-22 | 2026-11-22 | Implemented under the gate. Module-size gate required a split: DbCondition and the two classifiers moved to scripts/db/recovery_classification.py (labels only, no policy), and the import call sites in rotation.py, recovery_drill.py and the affected tests were updated. |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-22 | 2026-11-22 | Affected tests only, no assertion changes; test_db_recovery.py and test_db_maintenance.py are green after the import updates. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-22 | 2026-11-22 | $V |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-22 | 2026-11-22 | Documentation updated for the split in docs/41_db/db_07 sections 9.2 to 9.4 and ADR-008 Implementation References. |

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
- **Requirement ID**: REQ-003, REQ-005 (paths and recovery policy resolved through the owner-supplied typed configuration)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/db/recovery.py`
