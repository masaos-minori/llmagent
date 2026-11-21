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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Gated: issues/20261119-145303_cliplc005_staged-reload-transaction.md phase all - the typed-candidate model is defined by that Issue; coordination dependency, either order works |
| 2 | Add or update tests per Validation plan | Pending | — | — | Gated: same - affected test only, no assertion changes proven |
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
- **Requirement ID**: REQ-003, REQ-005 (paths and recovery policy resolved through the owner-supplied typed configuration)
- **Source issue**: issues/20261120-114212_agentcfg004_config-ownership-split.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-140444_agentcfg004_config-ownership-split.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-144837
- **Related target files**: `scripts/db/recovery.py`
