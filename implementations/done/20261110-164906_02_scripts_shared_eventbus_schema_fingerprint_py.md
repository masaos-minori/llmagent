## Goal

Delete `scripts/shared/eventbus_schema_fingerprint.py` after every caller has moved to the
generalized `scripts/shared/schema_fingerprint.py` (`REQ-002`, `REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2)

## Assumptions
- By Phase 2 all importers import `schema_fingerprint (new)` instead, so deleting this module
  does not break an import. Residue must be confirmed before deletion (AC-04 residue check).
- Execution order: batch mode runs members in seq order, so this deletion lands first inside
  the fingerprint-cutover unit; the importer moves are later members of the same unit — 03
  (`scripts/eventbus/schema.py:7`), 16 (rewrites the `deploy/init_db.sh:108` comment), 21
  (`tests/db/test_create_schema.py:26`, which also imports `apply_schema_in_memory`,
  `expected_fingerprint`, and `build_fingerprint` from this module), and 49
  (`scripts/eventbus/db_tools.py:25`). Until those members land, importer import failures are
  batch-allowed red states recorded in the Failure Log. The definitive importer-residue check
  runs at the unit-end Step 7 gate. The remaining name entry at
  `tests/mcp_servers/mdq/test_mdq_rag_boundary.py:74` is a string in an allowlist and does not
  break on deletion; row 33 removes it.
- This is a pure removal: no compatibility shim is added (Plan target note).

## Design decisions
- Delete the whole file including `assert_matches`, `validate_canonical`, `build_fingerprint`,
  and the `user_version` gate; none of these remain referenced after the cutover.

## Alternatives considered
- Keeping the file as dead code: rejected; the Issue removes the second mechanism (REQ-004).

## Implementation
### Target file
`scripts/shared/eventbus_schema_fingerprint.py` (delete)

### Procedure
1. Importer-residue check (unit-end gate, Step 7): `rg -n "eventbus_schema_fingerprint" scripts/ tests/ deploy/ tools/` must then return only the allowlist string entry in `tests/mcp_servers/mdq/test_mdq_rag_boundary.py` (removed by row 33); members 03, 16, 21, and 49 have moved the imports and rewritten the `deploy/init_db.sh:108` comment by then.
2. Remove the file: `git rm scripts/shared/eventbus_schema_fingerprint.py`.
3. Update the allowed-import entry in `tests/mcp_servers/mdq/test_mdq_rag_boundary.py:74` to the new module name (that row is handled by its own document).

### Method
- Run the residue grep BEFORE deletion; every hit must be reviewed and either already moved or scheduled in this Phase. The named `execution_snapshot.py` header `user_version` read is the only permitted remaining `user_version` reference (AC-04).
- Use `git rm` so the rename/delete is recorded.

### Details
- Do not leave a re-export shim anywhere; callers must import `from shared.schema_fingerprint import assert_matches`.

## Compatibility considerations
Callers that still import this module are out of scope for this Phase; they are moved in the same release unit (Phase 2).

## Security considerations
None; removal only.

## Rollback considerations
Revert the commit; `git restore` recreates the file.

## Validation plan
`rg -n "eventbus_schema_fingerprint" scripts/ tests/ deploy/ tools/` shows no live importer; full test suite passes.

## Completion criteria
`scripts/shared/eventbus_schema_fingerprint.py` no longer exists and no importer references it.

## Out of Scope
Moving callers (covered by their rows / this Phase's release unit).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-082800 | 20261111-082950 | git rm executed after residue grep confirmed only scheduled importers (rows 03, 21, 49, boundary allowlist row 33, init_db.sh comment row 16, egg-info build artifact). Allowed red state recorded: importers in those files break until their members land (batch mode). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-102849 | 20261111-102849 | adrrev005 batch cutover: full suite 12056 passed, 9 skipped; diff-cover 100%; pre-commit all pass |

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
- **Requirement ID**: `REQ-002` / `REQ-004` — delete the eventbus-named module after callers move
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/shared/eventbus_schema_fingerprint.py`
