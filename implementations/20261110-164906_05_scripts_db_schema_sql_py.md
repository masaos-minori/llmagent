## Goal

Expose the canonical DDL of every database through one accessor family in
`scripts/db/schema_sql.py`, and add the missing `build_eventbus_schema_sql()` accessor
(`REQ-002`, `REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `build_rag_schema_sql(dims: int)`, `build_session_schema_sql(dims: int)` (verified at lines
  161-169), and `build_workflow_schema_sql()` (verified at lines 241-243) already exist;
  callers pass their return value as canonical DDL. Fingerprint-gate callers must pass the
  deployed dims values (rag 1024, session 256) for the accessor to reproduce the canonical DDL.
- Verified 2026-11-11: plan 002 has already removed the eventbus accessor and every
  `PRAGMA user_version` reader from this file (`rg -n "user_version|eventbus_schema_version"
  scripts/db/schema_sql.py` returns no hit; file is 243 lines). Procedure step 2 is therefore
  a confirmation step, not a deletion step.
- Any eventbus accessor (`eventbus_schema_version`) in this file reads the removed stamp and
  must go; confirm current contents before editing.

## Design decisions
- Add `build_eventbus_schema_sql()` returning the canonical eventbus DDL text (read from `eventbus/schema.sql`), so eventbus has an accessor like the other domains and no caller reads `user_version` directly.
- Remove any `eventbus_schema_version`/`_VERSION_RE` helper and `PRAGMA user_version` reads from this file.

## Alternatives considered
- Reading `schema.sql` at each call site: rejected; one accessor family keeps the pattern uniform (Design).

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Add `build_eventbus_schema_sql()` alongside the existing accessors, returning the canonical
   eventbus DDL text (read from `scripts/eventbus/schema.sql`).
2. Confirm with `rg -n "user_version|eventbus_schema_version" scripts/db/schema_sql.py` that no
   `PRAGMA user_version` reader remains (already true after plan 002); delete any hit if one appears.
3. Point callers (handled by their rows) at these accessors for canonical DDL.

### Method
- Run `rg -n "user_version|eventbus_schema_version" scripts/db/schema_sql.py`; verified 2026-11-11 that there is no hit, so nothing to delete. Add `build_eventbus_schema_sql()` returning the canonical DDL text with the same `build_<domain>_schema_sql() -> str` shape.

### Details
- Keep the accessor family signature consistent (`build_<domain>_schema_sql() -> str`).

## Compatibility considerations
New accessor is additive; removed symbols are the eventbus `user_version` readers this Plan deletes.

## Security considerations
None; returns DDL text.

## Rollback considerations
Revert the commit.

## Validation plan
`uv run pytest tests/db/test_create_schema.py -v` passes; `rg -n "user_version" scripts/db/schema_sql.py` shows no reader.

## Completion criteria
`scripts/db/schema_sql.py` exposes a canonical DDL accessor per domain and contains no `user_version` reader.

## Out of Scope
Changing the DDL objects themselves.

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
- **Requirement ID**: `REQ-002` / `REQ-004` — expose canonical DDL accessors; remove the eventbus `user_version` reader
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/db/schema_sql.py`
