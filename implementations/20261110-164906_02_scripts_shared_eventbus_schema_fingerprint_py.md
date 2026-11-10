## Goal

Delete `scripts/shared/eventbus_schema_fingerprint.py` after every caller has moved to the
generalized `scripts/shared/schema_fingerprint.py` (`REQ-002`, `REQ-004`).

## Scope
**Release unit**: fingerprint-cutover (Phase 2)

## Assumptions
- By Phase 2 all importers import `schema_fingerprint` instead, so deleting this module does
  not break an import. Residue must be confirmed before deletion (AC-04 residue check).
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
1. Confirm every importer moved: `rg -n "eventbus_schema_fingerprint" scripts/ tests/ deploy/ tools/` returns only the self-reference in the deleted file (and the expected comment in `deploy/init_db.sh` line 108, which is rewritten in this Phase).
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
