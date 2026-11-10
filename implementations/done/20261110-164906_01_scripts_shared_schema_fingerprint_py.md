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
  and only required to exist by name (UNK-01; default in Implementation Intent). Confirmed
  with the real extension (`/opt/llm/sqlite-vec/vec0.so`) on 2026-11-11 against the rag,
  session, workflow, and eventbus canonical DDL: a fresh database built with the extension
  passes, and only the base names are required.

## Design decisions
- Generalize by threading the canonical DDL text through `assert_matches(conn, canonical_ddl (new), label=...)` instead of reading a fixed `schema.sql` path: the expected fingerprint is built by applying the canonical DDL text (the `canonical_ddl (new)` parameter) to a fresh in-memory database, then compared structurally. Callers pass DDL from `scripts/db/schema_sql.py`, `schema.sql`, or module constants.
- Coupled test edit (row `tests/mcp_servers/mdq/test_mdq_rag_boundary.py`): this cycle must add
  `"schema_fingerprint.py"` to the `ALLOWED` allowlist at line 74 (keeping the current
  `"eventbus_schema_fingerprint.py"` entry until row 2 deletes that module), otherwise
  `test_shared_layer_has_no_direct_mdq_rag_sqlite_access` fails the full suite as soon as the
  new module exists. Row 33 later removes the old entry.
- Reuse the eventbus module's normalization and comparison primitives (`build_fingerprint`, `_raise_first_difference`) unchanged; only the DDL source becomes a parameter.
- Corrected 2026-11-11 (Step 3a/3b finding, verified with the real `sqlite-vec` extension):
  the name filter cannot be a `_vec`/`_shadow` name heuristic. `rag` and `session` declare
  both `chunks_vec`/`memories_vec` (vec0) and `chunks_fts`/`memories_fts` (FTS5), whose
  shadows are named `{base}_data`, `{base}_config`, `{base}_docsize`, `{base}_idx`,
  `{base}_content` (FTS5) and `{base}_chunks`, `{base}_info`, `{base}_rowids`,
  `{base}_vector_chunks00` (vec0), and the vec0 shadow names are version-dependent.
  The rule is therefore: canonical DDL declares its virtual bases, each contributes a
  name-only entry, and the live side omits every `{base}_*` table and skips the shape
  comparison for the base itself.
- Applying vec0 DDL without the extension fails (`no such module: vec0`), so
  `apply_ddl_in_memory` strips every `CREATE VIRTUAL TABLE ...` statement before the
  in-memory apply (verified against the rag and session templates). Trigger bodies are
  unaffected: SQLite resolves them at execution time, so `chunks_ai`, `chunks_ad`,
  `chunks_au`, and `chunks_vec_ad` are created identically on both sides even though
  `chunks_fts` and `chunks_vec` are absent from the stripped script.
- Accepted limitation (recorded in the module docstring): a real table whose name falls
  under a virtual base's prefix (for example `chunks_vec_backup`) cannot be told apart
  from a shadow table and is omitted from the comparison.

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
- Public API (implemented 2026-11-11): `assert_matches(conn, canonical_ddl: str, *, label: str = "database")`, `expected_fingerprint(canonical_ddl: str) -> Fingerprint`, `apply_ddl_in_memory(canonical_ddl: str) -> Connection`, `build_fingerprint(conn) -> Fingerprint`, and the `REFUSAL_MESSAGE` constant.
- `_split_statements` splits the canonical script with `sqlite3.complete_statement` (a regular expression cannot tell a trigger body's semicolons from a statement end), and `_strip_virtual_statements` drops the virtual statements while returning their base names.
- Keep `_columns`, `_indexes`, `_foreign_keys`, `_triggers`, `_table_level_constraints`, `_normalize_ddl`, `build_fingerprint`, `_raise_first_difference` verbatim from the eventbus module; only the DDL source and the name-only handling in `_raise_first_difference` are new.
- Drop `_VERSION_STAMP_RE`, `_canonical_schema_version()`, `expected_fingerprint()` (the no-argument version), and `validate_canonical()` (the user_version gate is removed, REQ-004).

### Details
- Error message (implemented): each `_raise_first_difference` message names the first differing object and embeds `REFUSAL_MESSAGE` — "The database does not match the current schema. Automatic migration and version stamping are not supported. Stop the service, archive the existing database if required, remove or rename it, and create a new database using the current schema." — the same text the other databases use (`scripts/agent/services/workflow_schema.py:74-79`, `scripts/eventbus/schema.py:62-68`), so callers keep the existing match phrase `does not match the current schema`. Only schema structure is quoted, never row content.
- `tests/shared/test_schema_fingerprint.py` is the target file of its own row (row 19, executed next in this Plan's Phase 1); it covers missing CHECK constraint, extra legacy table, extra column, missing index, a trigger difference, and a vec virtual table satisfied by name, plus a matching database passing. This row creates the module only.

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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261111-073000 | 20261111-074520 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261111-074600 | 20261111-080021 | Deviation (shared with row 19, Plan step 1): row 01 unit tests live in row 19's target file tests/shared/test_schema_fingerprint.py, delivered there. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261111-080300 | 20261111-082253 | Shared full-suite run at the Plan step 1 boundary (deviation shared with row 19): run_validation_gates.py --full = all Pass (ast-grep Not run: binary absent on host). Deviation: coverage/diff-cover (>=90) gate run once for both rows. |

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