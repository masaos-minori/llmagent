## Goal

Follow the generalized fingerprint gate in `deploy/init_db.sh` (its row) inside the
EventBus deploy integration test (`REQ-003`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2; batched with rows 02,03,04,16,23,24,26 because the suite cannot validate green with the stamp removed until this row lands)

## Assumptions
- `deploy/init_db.sh` now gates EventBus through the generalized `scripts/shared/schema_fingerprint` gate (row 16); this test exercises that same path.
- Correction 2026-11-11 (fresh read): the earlier steps 1-2 referenced a stamp at line 59,
  an equality assertion at lines 76-77, and `test_refuses_shape_drift_at_current_version`;
  the real file stamps `user_version` in `_provision_databases`, has no version-equality
  assertion, and its drift cases are `test_init_db_malformed_aborts` /
  `test_shape_gate_rejects_malformed_isolated_from_create_schema_gate`. The procedure below
  follows the real file.
- With the generalized fingerprint gate, rag.sqlite and session.sqlite must exist in the
  sandbox (the gate checks all three domains), so the fixture provisions them and the stub
  copies the full scripts tree so the gate's `db.schema_sql`/`db.store_protocols` imports
  resolve.

## Design decisions
- Keep the sandbox driver that copies `scripts` and runs the real `init_db.sh`;
  only the assertions and fixtures follow the new gate.
- Drop the `PRAGMA user_version` stamp from the fixture: no version mechanism remains.

## Implementation
### Target file
`tests/deploy/test_init_db_eventbus_schema.py`

### Procedure
1. Delete the `PRAGMA user_version` stamp in `_provision_databases` and the
   `eventbus.db_tools.schema_version` import.
2. Provision rag/session (canonical builders + sqlite-vec extension) in the fixture, and
   copy the full scripts tree in `_write_stub_scripts` (create_schema.py stays a no-op).
3. Rename `test_init_db_malformed_stamped_aborts` to `test_init_db_malformed_aborts`; the
   drift cases keep asserting the abort through the generalized gate.

### Method
- Read the fixture and driver helpers (`_provision_databases`, `_write_init_db_driver`)
  with `rg -n 'user_version|schema_version|eventbus' tests/deploy/test_init_db_eventbus_schema.py`
  before editing; change only what the generalized gate requires.

### Details
- Do not add a separate EventBus fingerprint assertion here; the gate lives in
  `deploy/init_db.sh` (row 16) and this test covers its end-to-end behavior.

## Compatibility considerations
The `eventbus.db_tools.schema_version` import was removed here: the generalized gate
reports no version, so the fixture no longer stamps one.

## Security considerations
None beyond the existing sandbox isolation (`DEPLOY_SCRIPTS`/`DEPLOY_DB` overrides).

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/deploy/test_init_db_eventbus_schema.py -v` passes; the four drift
cases fail with the explicit archive-and-recreate error via the generalized gate.

## Completion criteria
The test follows the generalized gate, the version-equality assertion holds, and shape
drift is refused with the archive-and-recreate error.

## Out of Scope
Re-implementing the gate itself (`deploy/init_db.sh`, row 16).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the test to follow the generalized gate | Completed | — | 20261111-090541 | rewritten for delegation contract: init_db ignores eventbus, db_tools verify accepts/refuses; 3 tests pass |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-102849 | 20261111-102849 | adrrev005 batch cutover: full suite 12056 passed, 9 skipped; diff-cover 100%; pre-commit all pass |

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
- **Requirement ID**: `REQ-003` — follow the generalized gate in the EventBus deploy test
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/deploy/test_init_db_eventbus_schema.py`
