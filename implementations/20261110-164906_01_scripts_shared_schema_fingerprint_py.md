## Goal

Create `scripts/shared/schema_fingerprint.py`: a generalized schema shape validator that
takes canonical DDL text as input and compares the live database shape against it, raising
a Fail-Fast `RuntimeError` on any deviation (`REQ-002`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The eventbus module `scripts/shared/eventbus_schema_fingerprint.py` is the design source
  and stays in place until its callers move (REQ-002); this Plan deletes it in Phase 2.
- `shared` stays a leaf (stdlib only); the new module imports only the standard library, so
  `PYTHONPATH=scripts uv run lint-imports` keeps `shared-is-leaf`.
- sqlite-vec virtual tables and their shadow tables are excluded from the shape comparison
  and only required to exist by name (UNK-01; default in Implementation Intent).

## Design decisions
- Generalize by threading the canonical DDL text through `assert_matches(conn, canonical_ddl, label=...)` instead of reading a fixed `schema.sql` path: the expected fingerprint is built by applying `canonical_ddl` to a fresh in-memory database, then compared structurally. Callers pass DDL from `scripts/db/schema_sql.py`, `schema.sql`, or module constants.
- Reuse the eventbus module's normalization and comparison primitives (`build_fingerprint`, `_raise_first_difference`) unchanged; only the DDL source becomes a parameter.

## Alternatives considered
- A per-database validator per database: rejected by the Issue (one mechanism only).
- Keeping `user_version` as a first gate: rejected as a second mechanism (REQ-004).

## Implementation
### Target file
`scripts/shared/schema_fingerprint.py` (new)

### Procedure
1. Copy the eventbus module body into the new file.
2. Replace the fixed `_SCHEMA_PATH`/`_schema_sql()`/`apply_schema_in_memory()` source with a DDL-text parameter on the public entry points.
3. Add the unit test file `tests/shared/test_schema_fingerprint.py`.

### Method
- Signature change: `assert_matches(conn, canonical_ddl: str, *, label: str = "...")`; inside, build the expected fingerprint via a helper `apply_ddl_in_memory(canonical_ddl)` that runs `sqlite3.connect(":memory:")` + `executescript(canonical_ddl)`, then `build_fingerprint`, then `_raise_first_difference`.
- Keep `_columns`, `_indexes`, `_foreign_keys`, `_triggers`, `_table_level_constraints`, `_normalize_ddl`, `build_fingerprint`, `_raise_first_difference` verbatim.
- Drop `_VERSION_STAMP_RE`, `_canonical_schema_version()`, `expected_fingerprint()`, and `validate_canonical()` (the user_version gate is removed, REQ-004).
- Vec/shadow handling: `build_fingerprint` already lists every `table`/`view` from `sqlite_master`; add a name filter that requires vec virtual tables (e.g. names ending in `_vec`) and their `*_shadow`/`*_fts*` shadow tables to exist by name without comparing their shape (UNK-01). Document this in a docstring note.

### Details
- Error message must tell the operator to stop the service, archive the file, and recreate it (Design mechanism), matching the message used by the other databases.
- `tests/shared/test_schema_fingerprint.py`: missing CHECK constraint, extra legacy table, extra column, missing index, a trigger difference, and a vec virtual table satisfied-by-name each behave correctly; a matching database passes.

## Compatibility considerations
Existing callers still import `assert_matches`; their import path moves to this module in Phase 2 (see `scripts/shared/eventbus_schema_fingerprint.py` row). No runtime behavior changes for a matching database.

## Security considerations
Read-only inspection of the database via `PRAGMA`/`sqlite_master`; no data is written on refusal.

## Rollback considerations
Revert the commit; the module is new and unreferenced until Phase 2.

## Validation plan
`uv run pytest tests/shared/test_schema_fingerprint.py -v` passes for all drift kinds; `PYTHONPATH=scripts uv run lint-imports` keeps `shared-is-leaf`.

## Completion criteria
`scripts/shared/schema_fingerprint.py` exists with the DDL-parameterized `assert_matches`, `tests/shared/test_schema_fingerprint.py` passes, and `shared-is-leaf` is kept.

## Out of Scope
Deleting `scripts/shared/eventbus_schema_fingerprint.py` (Phase 2) and moving its callers.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: `REQ-002` — generalize the fingerprint into `scripts/shared/schema_fingerprint.py`
- **Source issue**: issues/20261109-112715_adrrev005_schema-fingerprint-unify.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-095137_adrrev005_schema-fingerprint-unify.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-164906
- **Related target files**: `scripts/shared/schema_fingerprint.py`
