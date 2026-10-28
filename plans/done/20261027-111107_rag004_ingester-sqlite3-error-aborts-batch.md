# Plan: Catch `sqlite3.Error` per URL group in `RagIngester._process_url_groups`

## Goal
- Make the ingestion batch honor its documented "log exceptions without stopping" contract for the
  SQLite error hierarchy: a `sqlite3.Error` raised while processing one URL group is logged and
  recorded as an unexpected failure, the remaining groups still process, and the post-ingestion
  consistency check still runs.

## Priority
Medium

## Scope
- **In-Scope**:
  - Adding `sqlite3.Error` to the `except` tuple in `RagIngester._process_url_groups` and the
    `import sqlite3` it requires.
  - A regression test driving `ingest_all`/`_process_url_groups` with a `sqlite3.OperationalError`
    on one group and asserting the remaining groups process and the consistency check runs.
  - Adding the DB-error row to the RagIngester error table in `docs/21_rag/rag_05_04-error-handling-reference.md`
    (the Issue's "Documentation Impact: None" is incomplete — see Problem).
- **Out-of-Scope**:
  - Broadening the catch to bare `Exception`/`BaseException` (carried from the Issue; forbidden by
    its Constraints).
  - Changing transaction boundaries or rollback behavior (`SQLiteHelper.begin_immediate` stays as-is;
    it already rolls back on any exception).
  - Changing `ingest_url_group`'s own exception semantics — the widening happens only in the
    batch loop, so direct callers of `ingest_url_group` keep current propagation.
  - The project-wide `int(cfg[...])` coercion style in `crawler.py`, `chunk_splitter.py`,
    `db/config.py`, `db/maintenance.py` (carried from the Issue as a separate concern).
  - httpx/transport error handling — verified contained inside `ChunkFactory.prepare` and converted
    to `failed_paths`; they never reach this handler (Issue Unresolved Question, answered: no change).
- **Dependencies**: N/A: self-contained method + test + doc row. Overlap notes:
  - `docs/21_rag/rag_05_04-error-handling-reference.md` is also a target of the rag003 Plan.
    Compatible: rag003 renames the `rag_service_url` occurrence in the RagPipeline table; this Plan
    adds a row to the RagIngester table. Disjoint sections; the second implementer rebases.
  - `tests/rag/ingestion/test_rag_ingester.py` and `scripts/rag/ingestion/ingester.py` appear in no
    other Frozen Plan's target table (verified by the cross-plan overlap check).

## Background
- `_process_url_groups` (`scripts/rag/ingestion/ingester.py`, verified at L370-380) loops over URL
  groups calling `self.ingest_url_group(...)` and catches only
  `(OSError, RuntimeError, ValueError)`, logging via `logger.exception` and appending
  `IngestUrlResult.unexpected_failure(url)`. Its docstring says "log exceptions without stopping";
  the module imports contain no `sqlite3`.
- `ingest_all` runs `doc_manager.check_consistency(...)` after `_process_url_groups` (verified at
  L169), so an escaping DB error skips the consistency gate.
- `sqlite3.Error` and all its subclasses (`OperationalError`, `IntegrityError`, `DatabaseError`,
  `ProgrammingError`, `DataError`, `InternalError`, `NotSupportedError`) derive from `Exception`,
  not from `OSError`/`RuntimeError`/`ValueError` (Python stdlib hierarchy; matches the Issue's
  empirical claim).
- `tests/rag/ingestion/test_rag_ingester.py::TestAtomicity::test_database_failure_during_replacement`
  (verified at L245-270) drives `ingest_url_group` directly with a patched
  `TransactionManager.commit` raising `sqlite3.DatabaseError` and asserts propagation — it does not
  go through `_process_url_groups`, so it is unaffected by the loop-level widening.
- Sibling precedent: `DocumentManager.check_consistency` already catches
  `(sqlite3.OperationalError, sqlite3.DatabaseError, ValueError)`.

## Problem
- A DB error on one URL group — busy timeout, disk full, integrity/unique violation, or an
  FTS5/`chunks_vec` write failure — escapes the loop, aborts every remaining group in the run, and
  skips `check_consistency`, while the docstrings promise no-stop behavior. Chunk files stay in
  `chunk_dir` (routing happens only on success), so the next run self-heals, but the current run
  silently drops work past the failing group.
- Corrected Issue claim: Documentation Impact "None expected" is incomplete —
  `docs/21_rag/rag_05_04-error-handling-reference.md` carries a per-component error table for
  `RagIngester` (verified: rows for embedding retry, `lang` `ValueError`, `fetched_at` errors) with
  no database-error row; once the catch explicitly covers `sqlite3.Error`, the reference should say
  so.

## Reason for Change
- Database errors are the most common transient/environmental batch failures (locks, disk, integrity),
  exactly the class the no-stop contract exists to survive. The fix aligns runtime behavior with the
  documented intent and with the sibling `check_consistency` handling.

## Implementation Intent
- Widen the loop-level catch to `(OSError, RuntimeError, ValueError, sqlite3.Error)` with
  `import sqlite3`; keep the existing `logger.exception` call and `IngestUrlResult.unexpected_failure`
  recording unchanged; add `sqlite3.Error` coverage via the base class rather than enumerating
  subclasses.

## Requirements
- `REQ-001`: `_process_url_groups` catches `sqlite3.Error` in addition to the existing three
  categories, with `import sqlite3` added to `scripts/rag/ingestion/ingester.py`; the catch stays
  bounded — no bare `Exception` or `BaseException`.
- `REQ-002`: On a caught DB error the behavior is identical to the existing unexpected-failure path:
  `logger.exception` logs with traceback, `IngestUrlResult.unexpected_failure(url)` is appended, and
  the loop continues to the next URL group; `ingest_all` then reaches `check_consistency`.
- `REQ-003`: `ingest_url_group` itself is unchanged: direct callers still see DB errors propagate
  (the TestAtomicity propagation test passes unmodified), and transaction rollback semantics in
  `SQLiteHelper`/`TransactionManager` are untouched.
- `REQ-004`: `docs/21_rag/rag_05_04-error-handling-reference.md` RagIngester table gains a row:
  `sqlite3.Error` during group processing → caught by `_process_url_groups`; skip URL group; `ERROR`
  (with traceback); continue with remaining groups; consistency check still runs.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/rag/ingestion/ingester.py | Add `import sqlite3` and extend the `_process_url_groups` except tuple with `sqlite3.Error` | The loop-level catch is the only batch boundary that decides whether one group's failure aborts the run | REQ-001, REQ-002, REQ-003 | `except (OSError, RuntimeError, ValueError):` at L377; module has no `sqlite3` import; docstring at L370 promises no-stop | tests/rag/ingestion/test_rag_ingester.py | Verified |
| tests/rag/ingestion/test_rag_ingester.py | Add the batch-continuation regression test | Issue Testing Expectations; no existing test drives `_process_url_groups`/`ingest_all` with a sqlite3 error (verified: the only DB-error test targets `ingest_url_group` propagation) | REQ-002, REQ-003 | `TestAtomicity::test_database_failure_during_replacement` (L245) asserts propagation from `ingest_url_group` directly | the file itself | Verified |
| docs/21_rag/rag_05_04-error-handling-reference.md | Add the DB-error row to the RagIngester error table | The per-component error table is the subsystem's error contract record; the new explicit catch must appear in it (corrects the Issue's "no docs impact") | REQ-004 | RagIngester table at L82-89 has no database-error row | N/A: documentation file | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/rag/ingestion/ingester.py `ingest_all` | Confirms `check_consistency` runs after `_process_url_groups` (L169) and the results it consumes | REQ-002 |
| tests/rag/ingestion/test_rag_ingester.py `TestAtomicity` | The propagation contract that must keep passing; shows the established fixture pattern (`_make_ingester`, mock db/doc_mgr/http client) to reuse in the new test | REQ-003, REQ-004 |
| scripts/rag/ingestion/document_manager.py `check_consistency` | Sibling catch precedent for the same error hierarchy | REQ-001 (design consistency) |
| scripts/db/helper.py `SQLiteHelper._begin_transaction` | Confirms rollback-on-any-exception is already correct and must not be touched | REQ-003 |
| scripts/rag/exceptions.py `ChunkFormatError` | Confirms it stays covered: it subclasses `ValueError`, so its current catch path is unaffected by adding `sqlite3.Error` | REQ-001 |

## Acceptance Criteria
- `AC-1` (REQ-001): The except tuple is `(OSError, RuntimeError, ValueError, sqlite3.Error)`; no
  other catch sites in the module are widened; bandit/ruff report no blind-except.
- `AC-2` (REQ-002): With two URL groups where the first raises `sqlite3.OperationalError`, the run
  returns results for both groups (first marked unexpected failure, second successfully ingested),
  the `ERROR` log with traceback is emitted for the failed group, and `check_consistency` is invoked.
- `AC-3` (REQ-003): `TestAtomicity::test_database_failure_during_replacement` passes unmodified;
  `ingest_url_group` still propagates `sqlite3.DatabaseError` to direct callers.
- `AC-4` (REQ-004): The RagIngester error table documents the DB-error row.
- `AC-5` (all REQs): Full ingestion test suite and the full `tests/` suite pass.

## Tests
- `REQ-002`: Unit regression — build an ingester with two chunk files for two URL groups
  (existing `_make_ingester` fixture pattern); patch the ingestion path so the first group's
  commit/insert raises `sqlite3.OperationalError("database is locked")`; assert:
  `_process_url_groups` (via `ingest_all`) returns 2 results, group 1 is
  `IngestUrlResult.unexpected_failure`, group 2 succeeds, `check_consistency` was called, and no
  exception escapes. Deterministic via patching — no wall-clock or real lock contention.
- `REQ-001`: Boundary — assert `issubclass(sqlite3.OperationalError, sqlite3.Error)` and that
  `sqlite3.Error` is not a subclass of the previous tuple (guards the Issue's hierarchy claim inside
  the test suite).
- Regression: `tests/rag/ingestion/test_rag_ingester.py` (all existing tests, unmodified except for
  fixtures the new test adds) and `tests/rag/ingestion/`.

## Documentation Impact
- Required: one added row in `docs/21_rag/rag_05_04-error-handling-reference.md`'s RagIngester table,
  per `docs/00_index.md`'s mapping of ingestion/error-path changes to the 21_rag error-handling
  reference. The Issue expected no docs impact; verification shows the component error table is the
  contract record and would be incomplete without the row (Problem). Module/method docstrings already
  state the no-stop intent and need no change.

## Assumptions
- Catching the `sqlite3.Error` base class (rather than enumerating `OperationalError`/`IntegrityError`/
  `DatabaseError` as `check_consistency` does) is the correct granularity here: the batch loop wants
  the whole hierarchy, and the base class is narrower than `Exception`, satisfying the Issue's
  Constraint. `check_consistency`'s narrower list is a different context (it also catches `ValueError`
  for data-shape errors) and is not modified.
- `sqlite3.Error` reaching `_process_url_groups` means the group's own transaction has already been
  rolled back by `SQLiteHelper`/`TransactionManager` (verified rollback-on-any-exception), so partial
  writes are not introduced by continuing the loop.
- Marking the failed group `unexpected_failure` (the existing generic classification) is acceptable
  for DB errors; introducing a dedicated failure reason is out of scope for this fix.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | No blocking unknowns. The Issue's Unresolved Question (httpx errors reaching this handler) is answered by verification: `ChunkFactory.prepare` contains embedding/HTTP failures as `failed_paths`. | — | — | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/rag/ingestion/ingester.py | Except tuple + import | All batch ingestion runs (`rag_ingester` service) | 1 | High (single author, 100%) | None: no new module or config; service restart via normal deploy only |
| tests/rag/ingestion/test_rag_ingester.py | New regression + boundary tests | Test suite only | 0 | High (single author, 100%) | None |
| docs/21_rag/rag_05_04-error-handling-reference.md | One table row | Docs domain 21_rag | 8 | High (single author, 100%) | None |

## Design
- **Widen at the loop, not at `ingest_url_group`**: the no-stop contract belongs to the batch
  boundary. Keeping `ingest_url_group` pure preserves the atomicity test's propagation contract and
  any future caller that wants fail-fast per-group semantics.
- **Base-class catch**: `sqlite3.Error` covers every DB failure the Problem lists without enumerating
  subclasses, and remains a bounded, intent-revealing catch (Constraint-compliant).
- **Same failure surface as existing categories**: logging and `unexpected_failure` recording are
  reused unchanged, so downstream consumers of `ingest_all` results (counts, diagnostics) see DB
  failures as the same result kind they already handle — no new result type.
- **Docs as contract**: adding the error-table row makes the widened boundary visible in the same
  place reviewers consult for the other categories, preventing a future "fix" from re-narrowing it.

## Implementation steps
1. **Phase 1: Characterization baseline**
   - [ ] Run `tests/rag/ingestion/test_rag_ingester.py` unchanged, recording current behavior of the
     TestAtomicity propagation tests (REQ-003).
2. **Phase 2: Widen the catch**
   - [ ] Add `import sqlite3` and extend the except tuple in `_process_url_groups` (REQ-001;
     `scripts/rag/ingestion/ingester.py`).
3. **Phase 3: Tests**
   - [ ] Add the two-group continuation test and the hierarchy boundary test (REQ-002, REQ-003;
     `tests/rag/ingestion/test_rag_ingester.py`).
4. **Phase 4: Docs, deployment check, and verification**
   - [ ] Add the RagIngester DB-error row (REQ-004;
     `docs/21_rag/rag_05_04-error-handling-reference.md`).
   - [ ] Deployment validation/scripts check: no new module, config key, or service change; the
     existing `rag_ingester` service restarts through normal deploy (REQ-001).
   - [ ] Run the full `rules/toolchain.md` validation sequence (all REQs).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/ingestion/ingester.py | Unit (patched DB failure) | `uv run pytest tests/rag/ingestion/test_rag_ingester.py` | Continuation + boundary tests pass; all pre-existing tests pass unmodified |
| scripts/rag/ingestion/ingester.py | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; no blind-except findings |
| All targets | Regression | `uv run pytest tests/` | Full suite green |
| docs/21_rag/rag_05_04-error-handling-reference.md | Documentation consistency (21_rag domain) | `rules/toolchain.md` documentation consistency check | Row present and matches implemented behavior |
| All targets | Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | New except branch covered |

## Risks
- **Risk**: swallowing a DB error masks a systemic corruption while the batch keeps writing →
  **Mitigation**: `logger.exception` keeps the full traceback; the group is recorded as a failed
  result (not silent); `check_consistency` runs at the end of every completed run and reports
  integrity damage; failed chunk files remain in `chunk_dir` for reprocessing.
- **Risk**: continuing after a locked/interrupted transaction leaves half-written state →
  **Mitigation**: verified `SQLiteHelper._begin_transaction` rolls back on any exception before the
  error reaches the loop; the new test asserts group isolation (second group unaffected).
- **Risk**: a `sqlite3.Error` that indicates a programming error (e.g. `ProgrammingError` from a bad
  SQL call) is now caught and keeps running → **Mitigation**: it is still logged with traceback and
  recorded as `unexpected_failure`, so it surfaces in results and logs; the constraint against a bare
  `Exception` keeps non-DB programming errors (e.g. `TypeError`, `AttributeError`) failing fast as
  today.
- **Risk**: doc file is shared with the rag003 Plan → **Mitigation**: disjoint tables (RagPipeline vs
  RagIngester); both Plans record the overlap as Compatible; second implementer rebases.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization baseline | Completed | — | — | Suite green; red-before-green confirmed for the regression |
| 2 | Phase 2: widen the catch | Completed | 20261028-071115 | 20261028-071116 | Procedure _01 archived |
| 3 | Phase 3: tests | Completed | 20261028-071800 | 20261028-072129 | Procedure _02 archived; direct `_process_url_groups` test |
| 4 | Phase 4: docs, deployment check, verification | Completed | 20261028-072300 | 20261028-073709 | Procedure _03 archived; docs check + full suite + diff-cover green |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261027-165951_01_scripts_rag_ingestion_ingester.py.md | 2 | Procedure | Completed | — | — |
| implementations/20261027-165951_02_tests_rag_ingestion_test_rag_ingester.py.md | 3 | Procedure | Completed | — | — |
| implementations/20261027-165951_03_docs_21_rag_rag_05_04-error-handling-reference.md.md | 4 | Procedure | Completed | — | — |
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-074526_rag004_ingester-sqlite3-error-aborts-batch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-111107
- **Related target files**: scripts/rag/ingestion/ingester.py, tests/rag/ingestion/test_rag_ingester.py, docs/21_rag/rag_05_04-error-handling-reference.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Problem (tuple verified at L377); Required Changes | scripts/rag/ingestion/ingester.py | Phase 2 | AC-1 | Continuation test + static checks | Confirmed by repository evidence |
| REQ-002 | Acceptance Criteria (logged, marked, continues, consistency runs); L169 verified | scripts/rag/ingestion/ingester.py | Phase 2 | AC-2 | Continuation regression test | Confirmed by repository evidence |
| REQ-003 | Constraints (transaction semantics); TestAtomicity verified | tests/rag/ingestion/test_rag_ingester.py | Phase 3 | AC-3 | Existing propagation test unmodified | Confirmed by repository evidence |
| REQ-004 | Verified gap in RagIngester error table (corrects Issue's "no docs impact") | docs/21_rag/rag_05_04-error-handling-reference.md | Phase 4 | AC-4 | 21_rag documentation consistency check | Confirmed by repository evidence |
| REQ-002 | Issue Testing Expectations | tests/rag/ingestion/test_rag_ingester.py | Phase 3 | AC-2 | New continuation + boundary tests | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-165951 -->