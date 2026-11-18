## Goal
- Make `RagMaintenanceService.rebuild_vec()` and `reconcile_url()` work on the canonical `rag.sqlite` schema and persist atomically, report `integrity_ok` from the integrity outcome only, and correct the `SQLiteHelper` docstring, with persistence tests that reopen the database.

## Priority
High

## Scope
- **In-Scope**: commit and rollback behavior of `rebuild_vec` and `reconcile_url`; making both repairs run against the canonical schema (no `chunks.embedding`, rows read by column name); the `integrity_ok` mapping of `recover()`; the `SQLiteHelper` class docstring; persistence and contract tests; aligning the existing fake-helper tests with the real helper.
- **Out-of-Scope**: choosing the RAG failure policy; changing repair action names or the consistency check messages; editing ADR or docs wording; `DbMaintenanceService.recover_session` (UNK-03); re-embedding chunks (UNK-01); `rebuild_fts` behavior.
- **Dependencies**: N/A: none. This Plan has no prerequisite. It is a soft prerequisite of the issue adrchk006 (rag-failure-policy), which relies on `rebuild_vec` persisting before its repair actions are corrected; that issue is named by id and not by path because it does not gate this Plan.

## Background
The ADR review reported that `rebuild_vec` and `reconcile_url` write under `write_mode=True` without a `commit()`, that `recover()` maps VACUUM failures to integrity failures, and that the `SQLiteHelper` docstring overstates the pragma behavior. Re-verification (Step 2) confirmed the missing commits and the docstring, and found that both repairs fail earlier on the canonical schema, which the existing tests hide.

## Problem
- `SQLiteHelper.close()` closes without committing, so an uncommitted write is discarded at exit. `rebuild_fts` commits; `rebuild_vec` and `reconcile_url` do not.
- On the canonical schema `rebuild_vec` raises `OperationalError: no such column: embedding` (the canonical `chunks` table has no `embedding` column; vectors exist only in `chunks_vec`), and `reconcile_url` raises `TypeError` because it reads rows by column name on a connection opened without `row_factory=True`. Reproduced in a scratch database with the canonical table shapes.
- The existing tests patch `SQLiteHelper` with a fake whose rows are `sqlite3.Row` and use a stand-in `chunks` table with an `embedding` column, so they pass.
- `recover()` sets `integrity_ok=result.success`; a VACUUM failure after a passing integrity check returns `success=False` with `action="vacuum_failed"`, so a healthy database is reported as failed. `recover()` has no caller in `scripts/` and no test.
- The `SQLiteHelper` class docstring says the pragmas apply to every connection; a read-only connection gets only `busy_timeout`.

## Reason for Change
- The vector repair action cannot work and, once it runs, would lose its writes; operators running `/session rag-rebuild-vec` get an exception.
- The Issue's Acceptance Criteria 1 and 2 assume chunks carry embeddings, which the canonical schema contradicts, so the criteria are restated in this Plan (REQ-002, REQ-003).
- Another open issue relies on `rebuild_vec` persisting before its repair actions are corrected.

## Implementation Intent
- Every maintenance write commits at the end of a successful repair and rolls back completely when the repair fails (the connection closes uncommitted).
- `rebuild_vec` removes vector rows that have no `chunks` row and keeps valid rows; `reconcile_url` rebuilds the URL's FTS rows and leaves vector rows untouched.
- `integrity_ok` reflects the integrity check only; secondary steps (VACUUM) are reported separately through `action`.
- Tests write first, fail first, and reopen the database with a new connection.

## Requirements
- `REQ-001`: `rebuild_vec` and `reconcile_url` commit at the end of a successful repair, and a failure inside either leaves the database unchanged for a new connection.
- `REQ-002`: `rebuild_vec` runs on the canonical schema: it removes `chunks_vec` rows whose `chunk_id` has no `chunks` row, preserves every valid row, and returns the number of `chunks_vec` rows remaining (UNK-01, UNK-02 defaults).
- `REQ-003`: `reconcile_url` runs on the canonical schema: it reads rows by column name through `row_factory=True`, rebuilds only the URL's `chunks_fts` rows, leaves `chunks_vec` untouched, and keeps its return shape (`{"found": False}` or `{"found": True, "chunks": n}`).
- `REQ-004`: `recover()` sets `integrity_ok` from the integrity outcome: `True` when the integrity check passed (including `action="vacuum_failed"`), and the existing values otherwise.
- `REQ-005`: The `SQLiteHelper` class docstring states that read-only connections apply only `busy_timeout` and that leaving the context closes the connection without committing.
- `REQ-006`: Persistence and `integrity_ok` tests run against a real database file, are written before the fix and fail on the pre-fix code, and the existing fake-helper tests honor the `row_factory` flag as the real helper does.
- `REQ-007`: A helper contract test pins that a write is discarded at context exit without `commit()` and persists with it.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `tests/db/test_sqlite_helper.py` | Helper commit contract test | Add a test that a write is discarded at context exit without `commit()` and persists with it | REQ-007 / AC-5 | `SQLiteHelper.close()` closes the connection without committing and `__exit__` calls it; the file exists with 6 commits in 30 days (checked in Step 2) | `uv run pytest tests/db/test_sqlite_helper.py` | Verified |
| `tests/agent/services/test_rag_maintenance_persistence.py` | Persistence and `integrity_ok` tests | New file: tests that reopen a real database file after `rebuild_vec`, `reconcile_url`, and an injected failure, and that map `recover()` results (written first, failing before the fix) | REQ-001, REQ-002, REQ-003, REQ-004, REQ-006 / AC-1, AC-2, AC-3, AC-5 | New file; the directory `tests/agent/services/` exists and has no RAG maintenance test file; the failures reproduced in a scratch database with canonical table shapes (checked in Step 2) | `uv run pytest tests/agent/services/test_rag_maintenance_persistence.py` | Verified |
| `tests/agent/services/test_rag_index_integrity.py` | Align the fake-helper tests | Route the patched helper's `open` through the fake's `open()` so `row_factory` is honored, and update the `rebuild_vec` and `reconcile_url` tests to the canonical contract | REQ-006 / AC-5 | Both tests patch `SQLiteHelper` with a mock whose `open().__enter__` returns the fake (rows stay `sqlite3.Row`) and use a stand-in `chunks` table with an `embedding` column (checked in Step 2) | `uv run pytest tests/agent/services/test_rag_index_integrity.py` | Verified |
| `scripts/db/helper.py` | Class docstring | Replace "applied to every connection" with the real pragma behavior and add that exit closes without committing | REQ-005 / AC-4 | The class docstring says WAL/synchronous/busy_timeout apply to every connection; `apply_connection_pragmas(read_only=True)` applies only `busy_timeout` (checked in Step 2) | `tests/db/test_sqlite_helper.py` | Verified |
| `scripts/agent/services/rag_maintenance_service.py` | Repair persistence and result mapping | Commit at the end of both repairs, make both run on the canonical schema, and set `integrity_ok` from the integrity outcome | REQ-001, REQ-002, REQ-003, REQ-004 / AC-1, AC-2, AC-3 | No `commit()` in `rebuild_vec` or `reconcile_url`; `rebuild_vec` selects `chunks.embedding`; `reconcile_url` reads `doc["doc_id"]` without `row_factory`; `integrity_ok=result.success` (checked in Step 2) | `tests/agent/services/test_rag_maintenance_persistence.py`, `tests/agent/services/test_rag_index_integrity.py` | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified. Same
one-file-per-row discipline as `Implementation Target Files` above — no directories,
glob patterns, components, file groups, or vague phrases.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/recovery.py` | `RecoveryResult` and the `vacuum_failed` action that `recover()` maps | REQ-004 |
| `scripts/db/schema_sql.py` | Canonical `rag.sqlite` DDL: `chunks` has no `embedding` column and `chunks_vec` is a vec0 table | REQ-002 |
| `scripts/rag/ingestion/transaction_commit.py` | Embeddings are written only to `chunks_vec` | REQ-002 |
| `scripts/agent/services/models.py` | `DbRecoverResult` fields | REQ-004 |
| `scripts/agent/services/db_maintenance_service.py` | Same `integrity_ok=raw.success` mapping for the session database; out of scope | UNK-03 |
| `scripts/agent/commands/cmd_session.py` | `/session rag-rebuild-vec` prints `chunks_vec rebuilt (N rows)` from the return value | REQ-002, UNK-02 |
| `tests/agent/commands/test_agent_cmd_session.py` | Mocks the service; shows the return value is consumed as a row count | UNK-02 |
| `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` | Describes `rebuild_vec` for orphan vector rows as removing rows with no matching chunk | REQ-002 |
| `docs/10_adr/adr_02_06_005_rag-source-derived-index-relationships.md` | Decision 9 and Decision 10 wording on rebuilding the vector index | UNK-01 |
| `docs/10_adr/adr_02_05_008_db-sqlite-4db-separation.md` | The `derived-data-rebuild` entry names `rebuild_vec()` | UNK-01 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): After `rebuild_vec()`, a new connection sees no `chunks_vec` row without a `chunks` row and every valid row; an injected failure inside the repair leaves `chunks_vec` unchanged for a new connection.
- `AC-2` (REQ-001, REQ-003): After `reconcile_url(url)`, a new connection sees the URL's chunks searchable through `chunks_fts` and `chunks_vec` unchanged; an unknown URL returns `{"found": False}`.
- `AC-3` (REQ-004): A VACUUM failure on a healthy database gives `integrity_ok=True` (test); a corruption that is not restored gives `integrity_ok=False`.
- `AC-4` (REQ-005): The `SQLiteHelper` class docstring no longer claims the pragmas apply to read-only connections and states the no-commit-on-exit behavior.
- `AC-5` (REQ-006, REQ-007): The persistence tests fail on the pre-fix code and pass after it; the helper contract test passes; the fake-helper tests honor `row_factory`.
- `AC-6` (REQ-001 to REQ-007): The validation sequence of `rules/toolchain.md` passes.

## Tests
- `REQ-001`, `REQ-002`, `REQ-003`: real-file tests in `tests/agent/services/test_rag_maintenance_persistence.py` using the canonical table shapes with a plain `chunks_vec` stand-in, a patched `SQLiteHelper` constructor that returns a helper for the temporary file, and a reopen with a new connection; one test injects a failure after the first write.
- `REQ-004`: tests that patch `recover_corruption` to return each relevant `RecoveryResult` and assert `integrity_ok`.
- `REQ-005`, `REQ-007`: a contract test in `tests/db/test_sqlite_helper.py`; the docstring is checked by review and `ruff`.
- `REQ-006`: `tests/agent/services/test_rag_index_integrity.py` keeps passing after its fake is aligned.

## Documentation Impact
N/A: the Issue requires no docs change beyond the `SQLiteHelper` docstring (REQ-005), and `docs/21_rag/rag_05_07-rag-index-consistency-checks.md` already describes orphan-row removal. The ADR wording question is UNK-01 and needs a maintainer approval record, so it is not edited here.

## Assumptions
- The repair contract of `rebuild_vec` on the canonical schema is the documented one: remove orphan vector rows, keep valid rows (UNK-01 default). The vector rows cannot be regenerated because the service has no embedder.
- `rebuild_vec` returns the number of `chunks_vec` rows remaining, so `/session rag-rebuild-vec` keeps its message without editing `cmd_session.py` (UNK-02 default).
- Commit follows `rebuild_fts`: one `db.commit()` at the end; the rollback on failure is the implicit rollback when the connection closes uncommitted, and a failure-injection test proves it. Alternative: `db.begin_immediate()` (BEGIN IMMEDIATE with explicit rollback); not chosen because the Issue and `rebuild_fts` use `commit()`.
- Tests use a plain `chunks_vec` table as the stand-in for the vec0 table (the sqlite-vec package is not installed in the dev environment), as the existing tests do; commit semantics do not depend on the table type.
- The persistence tests must not touch production paths: they patch the `SQLiteHelper` constructor in `agent.services.rag_maintenance_service` to open a temporary file.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The `rebuild_vec` contract on the canonical schema: orphan removal (documented in `rag_05_07`, default), a rebuild from source as ADR-005 Decision 9 and the ADR-008 `derived-data-rebuild` entry word it (needs an embedder, a new feature), or leaving vector repair out | Maintainer decision; an ADR wording change needs an approval record (ADR-005 already has a pending amendment) | The owner confirms the default before the `rebuild_vec` edit (first step of Phase 2); a different choice is a Plan amendment | False |
| UNK-02 | The return value of `rebuild_vec` (rows remaining, default) versus rows removed, which would need an edit to `cmd_session.py` outside the target files | Owner preference | The owner confirms with UNK-01; "rows removed" is a scope amendment | False |
| UNK-03 | `DbMaintenanceService.recover_session` maps `integrity_ok=raw.success` the same way for the session database (used by `/session recover`) | Owner decision on scope | A follow-up issue or a scope amendment; this Plan does not edit it | False |
| UNK-04 | `RagMaintenanceService.recover()` and `reconcile_url()` have no caller in `scripts/` | Whether they are reserved or dead (Unused Features rule) | The Plan fixes them as the Issue asks; the owner may instead remove them in a separate issue | False |

## Affected areas
`skills/DESIGN.md` Change-impact table, extended with `Churn (30d)` and `Bus Factor`
columns. The `File` column here MUST be a subset of `Implementation Target Files`'
rows — this table analyzes change-impact risk for those same files; it is not a
separate scope-of-record.

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `tests/db/test_sqlite_helper.py` | Modify | Low | 6 | High (single author) | not applicable (rsynced) |
| `tests/agent/services/test_rag_maintenance_persistence.py` | Create | Low | N/A: new file | N/A: new file | not applicable (rsynced) |
| `tests/agent/services/test_rag_index_integrity.py` | Modify | Low | 4 | High (single author) | not applicable (rsynced) |
| `scripts/db/helper.py` | Modify | High | 5 | High (single author) | not applicable (rsynced) |
| `scripts/agent/services/rag_maintenance_service.py` | Modify | Medium | 4 | High (single author) | not applicable (rsynced) |

## Design
- **Classification**: Path B (more than 3 files; changes the behavior of a public service API). Baseline: `radon cc` rates `reconcile_url` C (12) and every other method A; `vulture` and `bandit` report nothing on the two scripts targets; `lint-imports` keeps all contracts (checked in Step 3). Consumer scan for `rebuild_vec`, `reconcile_url`, and `integrity_ok`: the production consumer of `rebuild_vec` is `cmd_session.py` (a row count printed in a message); `reconcile_url` and `RagMaintenanceService.recover()` have no production caller; the other candidates are ADR and docs mentions and test citations recorded in `Reference Files` or `not affected: documentation or test citation only` (checked in Step 3). Persisted schema check: not applicable (no DDL, schema version, or migration change).
- **D1 Commit**: `db.commit()` after the last write of a successful repair, inside the `with` block and before the `return`; a failing repair raises, the context closes the connection, and the uncommitted transaction is discarded.
- **D2 `rebuild_vec`**: one statement removes `chunks_vec` rows whose `chunk_id` is not in `chunks`; the count of remaining rows is read after the delete. No embedding column is read. Alternative (UNK-01): re-embed from chunk text.
- **D3 `reconcile_url`**: open with `row_factory=True`; keep the FTS delete-and-insert for the URL's chunks; drop the vector delete and re-insert. Complexity falls from C (12) because the vector branch goes.
- **D4 `recover()`**: `integrity_ok = result.success or result.action == "vacuum_failed"`, with a one-line reason comment (the VACUUM runs only after a passing integrity check). `recovered` and `logical_ok` keep their mapping.
- **D5 Tests**: real database file in `tmp_path`; the canonical table shapes with a plain `chunks_vec`; a factory patched over `SQLiteHelper` that returns `SQLiteHelper(db_path=...)` for the file; a reopen with `sqlite3.connect`. Tests are written before the fix and shown failing (REQ-006).
- **D6 Docstring**: the class docstring names the connection modes: read-write connections get WAL, `synchronous=NORMAL`, and `busy_timeout`; read-only connections get only `busy_timeout`; leaving the context closes without committing, so callers commit.

## Implementation steps
1. **Phase 1: Failing tests and evidence**
   - [ ] Add the helper commit contract test to `tests/db/test_sqlite_helper.py` (REQ-007)
   - [ ] Create `tests/agent/services/test_rag_maintenance_persistence.py` with the persistence and `integrity_ok` tests and run it to show the failures (REQ-001, REQ-002, REQ-003, REQ-004, REQ-006)
   - [ ] Align the fake helper in `tests/agent/services/test_rag_index_integrity.py` with the real `row_factory` behavior and update its `rebuild_vec` and `reconcile_url` tests (REQ-006)
2. **Phase 2: Fix**
   - [ ] Confirm UNK-01 and UNK-02 with the owner before editing the repairs; stop if the owner chooses a different contract
   - [ ] Update the `SQLiteHelper` class docstring in `scripts/db/helper.py` (REQ-005)
   - [ ] Commit at the end of both repairs, make them run on the canonical schema, and map `integrity_ok` in `scripts/agent/services/rag_maintenance_service.py` (REQ-001, REQ-002, REQ-003, REQ-004)
3. **Phase 3: Validation and hand-off**
   - [ ] Run the Validation plan commands and report each result
   - [ ] Deploy hand-off: `scripts/` changes, so after the change is committed and pushed, deploying is the user's decision through `skills/deploy/SKILL.md`

### Release units
**Unit**: rag-repair-persistence | **Phases**: 1, 2 | **Reason**: the failing-first tests of Phase 1 stay red until the fix of Phase 2 lands, so neither phase can be validated alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/agent/services/test_rag_maintenance_persistence.py` | Unit, real database file | `uv run pytest tests/agent/services/test_rag_maintenance_persistence.py` | Fails before Phase 2 (record the failures), passes after |
| `scripts/agent/services/rag_maintenance_service.py`, `scripts/db/helper.py` | Lint, type, security, architecture | `uv run ruff format <files>`, `uv run ruff check <files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | No new findings |
| `tests/db/test_sqlite_helper.py`, `tests/agent/services/test_rag_index_integrity.py` | Unit | `uv run pytest tests/db/test_sqlite_helper.py tests/agent/services/test_rag_index_integrity.py tests/agent/commands/test_agent_cmd_session.py` | Pass |
| Whole change | Suite and coverage | `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | Pass; at least 90% on changed lines |
| `plans/`, `issues/`, `implementations/` | Work item checks | `uv run python tools/check_workitem_structure.py --file __CHANGED_FILES__`, `uv run python tools/check_workitem_traceability.py --active-only` | No findings |

## Risks
- **Risk**: Changing `rebuild_vec` from a "rebuild" to an orphan removal conflicts with ADR-005 Decision 9 and the ADR-008 wording → **Mitigation**: UNK-01 records the decision for the owner before the edit; the ADR wording is not edited here because it needs an approval record.
- **Risk**: Dropping the vector delete and re-insert from `reconcile_url` changes what it repairs → **Mitigation**: it never worked on the canonical schema (it raised), so no working behavior is lost; the Plan records the narrower contract (REQ-003) and the method has no production caller.
- **Risk**: A commit placed before the last write would persist a partial repair → **Mitigation**: commit is the last statement before the return, and the failure-injection test asserts an unchanged database after a mid-repair failure.
- **Risk**: A real-file test could touch production paths → **Mitigation**: the constructor patch points `SQLiteHelper` at a `tmp_path` file; `tests/conftest.py` isolation applies.
- **Risk**: `scripts/db/helper.py` has a wide blast radius (every DB user) → **Mitigation**: the change is a docstring only; the full suite runs once.
- **Risk**: Aligning the fake in `test_rag_index_integrity.py` could change other tests that share it → **Mitigation**: only the patched `open` of the two repair tests is routed through the fake's `open()`; the file's other tests keep their fixtures, and the whole file runs in Phase 1.
- **Risk**: The same `integrity_ok` defect remains in `DbMaintenanceService.recover_session` → **Mitigation**: UNK-03 hands it to the owner; it is not hidden.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for a freshly generated Plan (replace
with the Plan's actual steps once Implementation steps are broken down):

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Failing tests and evidence: helper contract test, persistence tests, fake-helper alignment | Pending | — | — | |
| 2 | Fix: docstring, repair commits and canonical-schema repairs, `integrity_ok` mapping | Pending | — | — | |
| 3 | Validation and hand-off | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261117-123007_adrchk007_rag-repair-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261118-112342
- **Related target files**: `tests/db/test_sqlite_helper.py`; `tests/agent/services/test_rag_maintenance_persistence.py`; `tests/agent/services/test_rag_index_integrity.py`; `scripts/db/helper.py`; `scripts/agent/services/rag_maintenance_service.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes (commit and rollback); `close()` does not commit (Step 2) | `tests/agent/services/test_rag_maintenance_persistence.py` | Phase 1 | AC-1, AC-2 | the new persistence tests | Confirmed by repository evidence |
| REQ-001 | Same | `scripts/agent/services/rag_maintenance_service.py` | Phase 2 | AC-1, AC-2 | the new persistence tests | Confirmed by repository evidence |
| REQ-002 | Canonical DDL has no `chunks.embedding`; `rag_05_07` orphan-removal contract (Step 2) | `tests/agent/services/test_rag_maintenance_persistence.py` | Phase 1 | AC-1 | the new persistence tests | Derived from confirmed evidence |
| REQ-002 | Same | `scripts/agent/services/rag_maintenance_service.py` | Phase 2 | AC-1 | the new persistence tests | Derived from confirmed evidence |
| REQ-003 | `reconcile_url` raises `TypeError` without `row_factory` (Step 2) | `tests/agent/services/test_rag_maintenance_persistence.py` | Phase 1 | AC-2 | the new persistence tests | Derived from confirmed evidence |
| REQ-003 | Same | `scripts/agent/services/rag_maintenance_service.py` | Phase 2 | AC-2 | the new persistence tests | Derived from confirmed evidence |
| REQ-004 | Issue Required Changes (`integrity_ok`); `vacuum_failed` action in `scripts/db/recovery.py` (Step 2) | `tests/agent/services/test_rag_maintenance_persistence.py` | Phase 1 | AC-3 | the new `integrity_ok` tests | Confirmed by repository evidence |
| REQ-004 | Same | `scripts/agent/services/rag_maintenance_service.py` | Phase 2 | AC-3 | the new `integrity_ok` tests | Confirmed by repository evidence |
| REQ-005 | Issue Required Changes (docstring); pragma behavior of `apply_connection_pragmas` (Step 2) | `scripts/db/helper.py` | Phase 2 | AC-4 | review and `ruff` | Confirmed by repository evidence |
| REQ-006 | Issue Testing Expectations; fake helper hides the defects (Step 2) | `tests/agent/services/test_rag_index_integrity.py` | Phase 1 | AC-5 | `uv run pytest tests/agent/services/test_rag_index_integrity.py` | Confirmed by repository evidence |
| REQ-006 | Same | `tests/agent/services/test_rag_maintenance_persistence.py` | Phase 1 | AC-5 | the new persistence tests fail before the fix | Confirmed by repository evidence |
| REQ-007 | Issue Required Changes (confirm no commit on exit) | `tests/db/test_sqlite_helper.py` | Phase 1 | AC-5 | `uv run pytest tests/db/test_sqlite_helper.py` | Confirmed by repository evidence |
