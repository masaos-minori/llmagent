## Goal

Replace the eventbus `user_version` cases in `tests/db/test_create_schema.py` with fingerprint
cases (`REQ-003`, `REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2; batched with rows 02,03,04,16,23,24,26 because the suite cannot validate green with the stamp removed until this row lands)

## Assumptions
- Current cases assert a `PRAGMA user_version` mismatch is refused (Plan: 50 hits); eventbus no
  longer gates on `user_version`.
- Verified 2026-11-11: this test also imports `eventbus.db_tools.schema_version` (line 25) and
  `apply_schema_in_memory`, `assert_matches`, `build_fingerprint`, `expected_fingerprint` from
  `shared.eventbus_schema_fingerprint` (lines 26-31). Row 49 KEEPS `schema_version` but re-derives
  it from an in-memory apply of the stamp-less DDL (correction 20261111: the earlier "row 49
  removes schema_version" was wrong); row 02 deletes the fingerprint module along with
  `apply_schema_in_memory` and `expected_fingerprint`. This row must land in the
  fingerprint-cutover batch BEFORE row 02, or the deletion breaks this test's imports.
- The EventBus fingerprint block at lines 1007-1044 calls `expected_fingerprint()` and
  `apply_schema_in_memory()`; `test_validator_raises_even_when_user_version_matches` (lines
  1192-1201) stamps `PRAGMA user_version = {eventbus_schema_version()}`.

## Design decisions
- Replace the eventbus `user_version` assertion with a fingerprint drift assertion (e.g. drop a column or add an extra table) expecting the archive-and-recreate error.
- Move imports to the generalized module: `from shared.schema_fingerprint import assert_matches, build_fingerprint`; build the expected fingerprint by applying the canonical eventbus DDL (`eventbus.db_tools.schema_sql()`, no stamp after row 04) to an in-memory database, replacing `apply_schema_in_memory()`/`expected_fingerprint()` calls.
- Delete or convert `test_validator_raises_even_when_user_version_matches`: the version gate no longer exists; keep the shape-drift guarantee through a drift mutation instead.

## Alternatives considered
- Deleting the eventbus case: rejected; keep coverage expressed through the fingerprint mechanism.

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Update the imports (lines 25-31): drop `eventbus.db_tools.schema_version`; import
   `assert_matches` and `build_fingerprint` from `shared.schema_fingerprint` instead of the
   deleted module; drop `apply_schema_in_memory` and `expected_fingerprint`.
2. Rewrite the EventBus fingerprint block (lines 1007-1044) to build the expected fingerprint
   from the canonical eventbus DDL text via the generalized module.
3. Find the eventbus `user_version` case(s) (including `test_validator_raises_even_when_user_version_matches`,
   lines 1192-1201); replace the `PRAGMA user_version` mutation with a shape drift.
4. Update assertions to expect the fingerprint refusal message.

### Method
- Mutate the created eventbus database shape (extra table/column) before re-opening via `create_schema`; assert refusal.

### Details
- Leave non-eventbus cases untouched.

## Compatibility considerations
Test-only; mirrors the `create_schema.py` / `schema.py` changes.

## Security considerations
None.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/db/test_create_schema.py -v` passes.

## Completion criteria
No `user_version` assertion remains for eventbus in this file; drift is covered by fingerprint cases.

## Out of Scope
Other databases' cases here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261111-084802 | imports moved to shared.schema_fingerprint; drift calls pass _CANONICAL_EVENTBUS_DDL; user_version case converted to init-path drift refusal |
| 2 | Add or update tests per Validation plan | Completed | — | 20261111-084803 | test file IS the deliverable; no separate test work |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261111-084803 | uv run pytest tests/db/test_create_schema.py -> 66 passed; full-suite gate rerun at unit end |

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
- **Requirement ID**: `REQ-003` / `REQ-004` — eventbus cases use fingerprint
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/db/test_create_schema.py`