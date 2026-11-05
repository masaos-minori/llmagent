## Goal
Regression guard for the canonical RAG fixture source `tests/db/test_rag_consistency.py`:
confirm it stays green after the recovery-drill release unit (proc 01 + proc 02) lands.
No code change to `tests/db/test_rag_consistency.py` is required.

The plan's row 03 assumed the drill reuses this file's builders; adversarial verification
(see below) found that assumption unrealized — the drill uses `scripts/db/schema_sql.py`
directly and keeps its plain-table fallback inline. Exposing public builder names or adding a production-equivalent wrapper would therefore
be unused API (no in-repo consumer; `tests/` is not on `sys.path`). Scope is reduced to
the regression guard per plan-owner decision.

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
Adversarial verification (Step 3a) found the plan's premise unrealized; see the finding
above. Per plan-owner decision the scope is reduced to a regression guard:

1. Verify the finding against live source (done in Step 2/3a): `test_recovery_drill.py`
   imports `build_rag_schema_sql`/`build_session_schema_sql` from `db.schema_sql` and keeps
   its plain-table fallback inline; it imports nothing from `test_rag_consistency.py`.
   `tests/` is not on `sys.path` (only `scripts/` and `tools/`), so siblings cannot import
   this file as a module. No in-repo consumer of the proposed public builder names
   exists.
2. Implement: **no change** to `tests/db/test_rag_consistency.py`. Exposing public builder
   names or adding a production-equivalent wrapper would be unused API and is dropped.
3. Validate: `uv run pytest tests/db/test_rag_consistency.py` stays green (AC-002
   regression guard).

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
- Existing RAG consistency tests remain green after the release unit lands (regression
  guard). No builder-exposure or production-builder addition is performed.

## Out of Scope
- Changing `check_rag_consistency` logic (`ragverify001`).
- Modifying `_RAG_SCHEMA`'s vec-avoiding behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change | Completed | 20261105-181000 | 20261105-181000 | N/A: no code change — scope reduced to regression guard; exposing builders / rag_production_schema would be unused API (adversarial finding) |
| 2 | Add or update tests | Completed | 20261105-181000 | 20261105-181000 | N/A: no test change needed |
| 3 | Run the validation sequence | Completed | 20261105-181000 | 20261105-181000 | existing test_rag_consistency.py stays green |
| 4 | Update documentation | Completed | 20261105-181000 | 20261105-181000 | N/A: procedure-doc correction only; no docs/00_index.md task-scope mapping |

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
