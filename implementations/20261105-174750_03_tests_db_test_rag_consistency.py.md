## Goal
Expose the canonical RAG fixture builders in `tests/db/test_rag_consistency.py` for
reuse by the drill test, and reconcile the fixture source with AC-002's requirement
that fixtures carry real FTS and vector structures.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- `tests/db/test_rag_consistency.py` already builds the in-memory RAG fixtures used
  by the consistency unit tests: `_make_rag_db()` returns a `_FakeSQLiteHelper`
  wrapping an in-memory `sqlite3` connection; `_insert_doc` / `_insert_chunk` insert
  rows. These are module-private (underscore-prefixed).
- `scripts/db/schema_sql.py` is the DDL SSOT; `build_rag_schema_sql(dims)` returns
  the production rag schema including real `chunks_fts` (fts5) and `chunks_vec`
  (vec0).
- The drill test builds **file-based** isolated copies and runs
  `check_rag_consistency` against a real `SQLiteHelper` connection, not an
  in-memory `_FakeSQLiteHelper`.

## Adversarial verification finding — discrepancy with the plan
The plan's row 03 states this file "builds canonical RAG fixtures ... for FTS and
vector structures" and cites it as the fixture source for REQ-002 / AC-002. Current
source contradicts this:

- `_RAG_SCHEMA` (`L33-L78`) contains the comment
  `# chunks_vec replaced with a plain table to avoid vec0 extension` and declares
  `chunks_vec` as a **plain** table (`L52-L54`), not a `vec0` virtual table.
- Therefore the existing builders cannot represent real vector data and cannot
  prove AC-002's "missing vec rows" damage case. They exercise the consistency-check
  *logic* against a controlled fake, which is their actual purpose.

Reconciliation: expose the existing builders for the non-vec consistency path, and
add a separate production-equivalent builder derived from `schema_sql.py` (real
fts5 + vec0) for the drill's AC-002 path. Do **not** convert `_RAG_SCHEMA` to vec0 —
the existing consistency tests depend on the plain-table behavior.

## Design decisions
- **Expose existing builders as public names.** Rename `_make_rag_db`, `_insert_doc`,
  `_insert_chunk` to public forms (or add public aliases) so siblings can import
  them without duplicating the schema. Keep the underscore-private originals for the
  existing internal tests, or migrate those tests to the public names.
- **Add a production-equivalent builder for AC-002.** Add a public
  `rag_production_schema(dims: int) -> str` returning `build_rag_schema_sql(dims)`
  and a builder that materializes it into a file connection, so the drill has a
  single canonical vec-carrying source. This is distinct from `_RAG_SCHEMA` and
  lives alongside it.
- **Single source of truth.** Both the consistency tests and the drill reference the
  exposed builders, preventing schema drift between the two files.

## Alternatives considered
- **Convert `_RAG_SCHEMA` to real vec0.** Rejected: the existing consistency tests
  rely on the plain-table `chunks_vec`; changing it breaks them. A separate builder
  is required regardless.
- **Derive drill fixtures only from `schema_sql.py` (no exposure here).** Possible,
  but then `test_rag_consistency.py` — the issue's named fixture source — gains no
  maintainability benefit and the two files could drift.

## Implementation
### Target file
`tests/db/test_rag_consistency.py`

### Procedure
1. Verify the finding above against live source before editing (`_RAG_SCHEMA`
   `L33-L78`, `chunks_vec` plain table `L52-L54`).
2. Expose the existing builders. Convert the three private helpers to public names
   and update the internal callers within this file:
   - `_make_rag_db()` → `make_rag_db()` (returns `_FakeSQLiteHelper`)
   - `_insert_doc(db)` → `insert_doc(db)`
   - `_insert_chunk(db, doc_id, content)` → `insert_chunk(db, doc_id, content)`
   Add module docstring notes that these build the **non-vec** consistency-test
   fixture (plain `chunks_vec`), distinct from the production builder below.
3. Add the production-equivalent builder for the drill's AC-002 path:
   ```python
   from db.schema_sql import build_rag_schema_sql

   def rag_production_schema(dims: int) -> str:
       """Production-equivalent rag DDL with real fts5 + vec0 (DDL SSOT).

       Distinct from _RAG_SCHEMA, which uses a plain chunks_vec table to avoid the
       vec0 extension. Use this for fixtures that must carry real vector structures
       (e.g. the recovery-drill negative cases).
       """
       return build_rag_schema_sql(dims)
   ```
   Optionally add a materializer that creates a file connection with this schema for
   the drill to restore against.
4. Confirm with the plan owner whether row 03 intends (a) only exposing the existing
   non-vec builders, or (b) also adding the vec-carrying production builder above.
   This procedure implements (b), which is required to satisfy AC-002.

### Method
- Keep the vec-avoiding `_RAG_SCHEMA` untouched; add the vec-carrying builder as a
  separate, clearly-named symbol so the two schemas are never confused.
- Public names are importable by `tests/db/test_recovery_drill.py`.

### Details
- Current line map: `_FakeSQLiteHelper` `L17`; `_RAG_SCHEMA` `L33-L78`; plain
  `chunks_vec` `L52-L54`; `_make_rag_db` `L81-L86`; `_insert_doc` `L89-L96`;
  `_insert_chunk` `L99-L106`.
- `build_rag_schema_sql(dims)` needs a concrete dimension; pick a small value
  (e.g. 128) for fixture speed.

## Compatibility considerations
- Renaming the private helpers changes this file's internal API. Update all internal
  callers (the `TestRagConsistency` classes at `L142`, `TestRagConsistencySeverity`
  at `L248`, etc.) to the public names, or keep private aliases so external imports
  do not break. Prefer direct migration since nothing outside this file imports
  them today.
- Adding `rag_production_schema` (new) is purely additive; existing tests are unaffected.

## Security considerations
- Test-only change; no runtime or data-path impact.

## Rollback considerations
- Reverting restores the private-builder names and removes the added builder. No
  service or config change is involved.

## Validation plan
- `uv run pytest tests/db/test_rag_consistency.py` — existing consistency tests stay
  green after the rename (AC-002 regression guard).
- `uv run pytest tests/db/test_recovery_drill.py` — the drill's production-equivalent
  rag fixture passes and the missing-vec damage fixture fails with integrity ok.
- Full suite + coverage gate and static gates per `rules/toolchain.md`.

## Completion criteria
- Existing RAG fixture builders are importable by sibling tests.
- A canonical vec-carrying production RAG builder exists for AC-002, derived from
  `schema_sql.py`.
- Existing consistency tests remain green.

## Out of Scope
- Changing `check_rag_consistency` logic (`ragverify001`).
- Modifying `_RAG_SCHEMA`'s vec-avoiding behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Expose canonical RAG fixture builders for reuse | Pending | — | — | |
| 2 | Add production-equivalent vec-carrying builder (AC-002) | Pending | — | — | Decision point (see Finding) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|-----|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`
- **Source issue**: `issues/20261104-143443_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261104-232133_drillmetrics001_strengthen-recovery-drills-and-rpo-rto.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-174750
- **Related target files**: `tests/db/test_rag_consistency.py`
```

## Notes on filling sections

- **The plan's fixture-source claim is inaccurate for vec.** Record the finding above
  and reconcile by exposing the non-vec builders while adding a vec-carrying
  production builder. Confirm scope with the plan owner (step 4).
- **Line numbers are guidance.** Verify against live source before editing.
