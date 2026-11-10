## Goal

Follow the generalized fingerprint gate in `deploy/init_db.sh` (its row) inside the
EventBus deploy integration test (`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `deploy/init_db.sh` now gates EventBus through the generalized `scripts/shared/schema_fingerprint` gate (row 16); this test exercises that same path.
- The fingerprint ignores `user_version`, so the canonical stamp the fixture writes is
  harmless (Plan Assumptions).

## Design decisions
- Keep the sandbox driver that copies `scripts/eventbus` and runs the real `init_db.sh`;
  only the assertions follow the new gate.

## Alternatives considered
N/A: documentation/test-only row; the wording follows the Plan's settled behavior.

## Implementation
### Target file
`tests/deploy/test_init_db_eventbus_schema.py`

### Procedure
1. The fixture stamps `PRAGMA user_version` at line 59; leave it (ignored by the
   fingerprint, harmless per the Plan).
2. The equality assertion at lines 76-77 still compares against
   `db_tools.schema_version()`; keep it — the generalized gate does not change the
   reported current version.
3. The shape-drift path (`test_refuses_shape_drift_at_current_version`) still raises the
   archive-and-recreate error through the generalized gate.

### Method
- Read the fixture and driver helpers (`_provision_databases`, `_write_init_db_driver`)
  with `rg -n 'user_version|schema_version|eventbus' tests/deploy/test_init_db_eventbus_schema.py`
  before editing; change only what the generalized gate requires.

### Details
- Do not add a separate EventBus fingerprint assertion here; the gate lives in
  `deploy/init_db.sh` (row 16) and this test covers its end-to-end behavior.

## Compatibility considerations
The `eventbus.db_tools.schema_version` import at line 26 stays; the generalized gate
reports the same current version.

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
| 1 | Update the test to follow the generalized gate | Pending | — | — | |
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
- **Requirement ID**: `REQ-003` — follow the generalized gate in the EventBus deploy test
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `tests/deploy/test_init_db_eventbus_schema.py`
