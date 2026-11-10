## Goal

Delete the `PRAGMA user_version` refusal cases from the EventBus db_tools test that this
Plan removes; keep the shape-drift case (`REQ-004`, fallout 2026-11-10).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `scripts/eventbus/schema.py` no longer compares `user_version` (row 3); the generalized
  fingerprint ignores it, so a stale or unstamped database is refused only on shape drift,
  not on version.

## Design decisions
- Remove the two version-refusal tests; keep the shape-drift test.

## Alternatives considered
N/A: fallout test row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/eventbus/test_eventbus_db_tools.py`

### Procedure
1. Delete `test_refuses_stale_version` (around lines 82-90): it sets
   `PRAGMA user_version = {version - 1}` and asserts `match="does not match the current
   schema"`; that refusal no longer fires once version is ignored.
2. Delete `test_refuses_unstamped_existing_database` (around lines 91-103): it sets
   `PRAGMA user_version = 0` and asserts `match="user_version 0"`; that refusal no longer
   fires.
3. Keep `test_refuses_shape_drift_at_current_version`: it alters a table shape and still
   raises the archive-and-recreate error through the generalized fingerprint.

### Method
- Confirm the case boundaries with
  `rg -n 'test_refuses_stale_version|test_refuses_unstamped|test_refuses_shape_drift|PRAGMA user_version' tests/eventbus/test_eventbus_db_tools.py`
  before editing.

### Details
- After deletion, `rg -l 'user_version' tests/eventbus/` should return nothing here; the
  named `execution_snapshot` exception is outside this file.

## Compatibility considerations
The `_state` helper and the kept shape-drift case stay.

## Security considerations
None.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/eventbus/test_eventbus_db_tools.py -v` passes; the shape-drift case
still refuses with the explicit error.

## Completion criteria
No test asserts the removed `user_version` refusal; the shape-drift case remains.

## Out of Scope
Changing `db_tools.py` (its row) or `schema.py` (row 3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the PRAGMA user_version refusal cases | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` — delete the user_version refusal cases (fallout)
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/eventbus/test_eventbus_db_tools.py`
