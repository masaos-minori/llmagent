## Goal

Remove `RagMaintenanceService`'s `corpus_identity()` wrapper so the maintenance service no
longer wraps `ensure_corpus_meta()` (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The wrapper is a thin method over `rag.corpus_identity.ensure_corpus_meta`, imported at
  the top of the module alongside `CorpusIdentity`.
- No other maintenance method calls `corpus_identity()`.

## Design decisions
- Delete the `corpus_identity()` method, the `NOTE (RAGCORPUS001...)` comment above it, and
  the `ensure_corpus_meta` name from the multi-line import; keep `CorpusIdentity` if still
  referenced, otherwise drop it too.

## Alternatives considered
N/A: removal is the decided Option B; a stub would keep a dead wrapper.

## Implementation
### Target file
`scripts/agent/services/rag_maintenance_service.py`
### Procedure
- Delete the `# NOTE (RAGCORPUS001, doc 06): ...` comment block above the method (lines
  60-63 plus its trailing blank line).
- Delete the `def corpus_identity(self, *, embedding_model_id, schema_version) -> ...`
  method (lines 65-81).
- Remove `ensure_corpus_meta` from the `from rag.corpus_identity import (CorpusIdentity,
  ensure_corpus_meta)` import (~line 16); drop `CorpusIdentity` as well if it is now unused.
### Method
Method plus comment plus import-name deletions; confirm no remaining reference to
`corpus_identity` or `ensure_corpus_meta`.
### Details
- Re-check whether `CorpusIdentity` is still used after removing the method; if not, remove
  it from the import too so `lint-imports` stays clean.

## Compatibility considerations
N/A: internal maintenance method removal; no external contract.

## Security considerations
N/A: no security-relevant behavior change.

## Rollback considerations
Revert the commit.

## Validation plan
- `rg -n "corpus_identity|ensure_corpus_meta" scripts/agent/services/rag_maintenance_service.py`
  returns nothing.
- `uv run pytest tests/agent/services/test_rag_index_integrity.py` passes.

## Completion criteria
`RagMaintenanceService` has no `corpus_identity()` method and imports no
`ensure_corpus_meta`; the integrity tests pass.

### Companion test files
- `tests/agent/services/test_rag_index_integrity.py`
  - Procedure: remove the docstring bullets (lines 12-13), the `_RAG_META_EXTRA` extra DDL
    block with its comment (lines 79-92), the `corpus_identity()` test section — section
    comment, `from rag.corpus_identity import CorpusIdentity` (line 534), `_rag_conn()`
    helper (line 538), and the two tests (lines 547-580).
  - Do NOT remove the `_SCHEMA_SQL_CANONICAL` `rag_corpus_meta` DDL and its INSERT seed
    (lines 97-168): the consistency tests run through `_check_schema_recognition()`, which
    `assert_matches` the fixture DB against `build_rag_schema_sql()` (`scripts/db/rag_consistency_queries.py:279`).
    The seed must be removed in the same cycle as the seq 13 `schema_sql.py` template edit
    (phase 8), or the fingerprint gate raises on the fixture.
  - Validation: `uv run pytest tests/agent/services/test_rag_index_integrity.py` passes with
    the canonical seed still matching the unedited template.

## Out of Scope
The identity module deletion (`REQ-006`, seq 08/09) and the maintenance-wrapper consumer in
other services.

## Execution Notes (2026-11-13)
- Executed against the Phase 3 variant (`cfb666e15`): wrapper
  `corpus_identity(self, *, embedding_model_id, schema_version) -> CorpusIdentity | None`
  over `ensure_corpus_meta` via `SQLiteHelper("rag")`. Method, its NOTE block, and the
  whole import line `from rag.corpus_identity import CorpusIdentity, ensure_corpus_meta`
  (single-line form; both names became unused) deleted.
- Companion: the wrapper tests at execution time patch `SQLiteHelper` with a
  `_FakeSQLiteHelper` connection (plan quoted an earlier monkeypatch variant); removed the
  whole section plus `from rag.corpus_identity import CorpusIdentity` and `_rag_conn()`.
  Docstring bullets and `_RAG_META_EXTRA` removed. `ruff format` applied after deletions.
- `_SCHEMA_SQL_CANONICAL` untouched in this procedure; its copied `rag_corpus_meta` DDL
  block AND the trailing seed INSERT must both be removed together with seq 13 (the
  fixture is fingerprint-compared against the template in both directions).
- Cross-file gap found at unit end: `docs/00_governance/governance_05_change-impact-and-
  dependency-graphs.md` claimed an `Agent → RAG` edge existing "only through" this module's
  `rag.corpus_identity` import. The import is now gone, so the edge was dropped from the
  confirmed-edge list and the paragraph rewritten as "Not an edge" (not covered by any
  procedure row; fixed 2026-11-13, `check_dependency_graph_cycles.py` passes with 6 edges).
- `uv run pytest tests/agent/services/test_rag_index_integrity.py` -> 8 passed;
  `uv run ruff check`/`ruff format --check`, `uv run mypy --strict` clean; background full
  suite `12169 passed, 9 skipped`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261113-102258 | 20261113 | executed; see Execution Notes |
| 2 | Add or update tests per Validation plan | Completed | — | 20261113 | Covers companion `test_rag_index_integrity.py` executed; see Execution Notes |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261113 | executed; see Execution Notes |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261113 | executed; see Execution Notes |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261110-170753_rmcompat003_rag-corpus-identity-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261112-120011_rmcompat003_rag-corpus-identity-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261112-223151
- **Related target files**: `scripts/agent/services/rag_maintenance_service.py`, `tests/agent/services/test_rag_index_integrity.py`