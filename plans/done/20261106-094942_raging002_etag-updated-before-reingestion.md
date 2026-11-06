# Update document ETag only after re-ingestion commits

## Goal
- Make the `documents` row's `etag`/`last_modified`/`fetched_at` freshness change atomically with the chunk replacement, so a failed re-ingestion can never leave the row claiming freshness the stored chunks do not have.

## Priority
High

## Scope
- **In-Scope**: removal of the pre-commit etag write in `DocumentManager.handle_existing_document`; guarded freshness value selection inside the `TransactionManager.commit` replace branch; regression and atomicity tests; doc description update.
- **Out-of-Scope**: `http_fetcher.py` conditional-request logic; the retry/ re-queue design (issue `20261106-073538_raging005_retry-dir-no-consumer.md`); `ETagManager` log-string wording (filed as `20261106-073538_raging008_etagmanager-stale-log-error.md`).
- **Dependencies**: N/A: none

## Background
For changed HTTP documents, `DocumentManager.handle_existing_document` calls `_update_etag` (→ `ETagManager.update`, `document_manager.py:101`, `:104-112`) and then returns `replace=True`. That UPDATE commits immediately, before `ChunkFactory.prepare` (embedding) and `TransactionManager.commit` run (`ingester.py:281-317`). On the success path, `TransactionManager.commit` deletes the document chain and re-inserts the `documents` row with the payload's `etag`/`last_modified`/`fetched_at` (`transaction_commit.py:57-78`, `document_persistence.py:77-95`), so the pre-commit write is redundant. On the failure path (embedding failure or transaction error) the commit never runs, and the row keeps the new etag while the old chunks remain. `HttpFetcher.get_conditional_headers` then sends that etag as `If-None-Match` and `fetch_html` returns `None` on 304 (`http_fetcher.py:39-77`), so the URL is never re-fetched. Verified line-by-line against HEAD `bdb9bed66` in Step 2 of this cycle.

## Problem
A failed re-ingestion leaves old chunks in place while the `documents` row carries the new etag. The next crawl receives HTTP 304, the URL is skipped forever, and the RAG index serves stale content with no automatic recovery path.

## Reason for Change
Data-integrity defect in the normal HTTP update workflow; the failure is self-perpetuating — no future crawl or ingest run can recover it without manual intervention.

## Implementation Intent
Remove the freshness write from `handle_existing_document`'s replace branch entirely: the only freshness write on the replace path is the `documents` insert, executed inside the same `BEGIN IMMEDIATE` transaction that deletes and re-inserts the document and chunks. Carry `ETagManager`'s stale-guard semantics into that insert: inside the transaction, resolve which freshness values win (incoming payload vs. stored row) before the delete, and insert the resolved values.

## Requirements
- `REQ-001`: `DocumentManager.handle_existing_document` performs no DB write on the HTTP replace branch — delete the `_update_etag` call (`document_manager.py:101`), the `_update_etag` method (`:104-112`), and the now-unused `ETagManager` import; the method's return contract is unchanged.
- `REQ-002`: `ETagManager` exposes `resolve_incoming(etag, last_modified, new_fetched_at) -> tuple[etag, last_modified, fetched_at]` that selects incoming vs. stored values with the existing guard rules (empty `new_fetched_at` raises `ValueError`; invalid timestamps raise `InvalidIncomingTimestampError`/`InvalidStoredTimestampError`; stale incoming or both-`None` incoming keep stored values; no stored row keeps incoming). `update()` delegates its guard decision to the same shared logic with unchanged observable behavior.
- `REQ-003`: `TransactionManager.commit`'s replace branch, inside `begin_immediate()`, resolves the freshness values via `ETagManager(self._db, doc_id).resolve_incoming(...)` against the current row before `delete_existing_document`, and `DocumentStore.insert` carries the resolved `etag`/`last_modified`/`fetched_at`; a stale payload can never regress stored freshness, and no freshness write lands unless the whole transaction commits.
- `REQ-004`: Regression tests cover: (a) existing HTTP document + changed etag + forced embedding failure → stored `etag`/`fetched_at` unchanged and a second run re-processes the URL; (b) transaction abort → both `documents` and `chunks` rows at pre-run values; (c) fresh payload → insert carries the new freshness values; (d) stale payload → insert carries the stored freshness values; (e) `resolve_incoming` unit coverage of the guard rules.
- `REQ-005`: Update `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`'s description of when `etag`/`last_modified` are refreshed (currently "otherwise the ETag fields are refreshed and the chunks are replaced", line 36) to describe the commit-boundary ordering and the guard applied at insert.

## Implementation Target Files
**Freeze status**: Frozen (Step 8b validation passed 20261106-094942 — every row `Verified`).

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Modify | Delete the pre-commit `_update_etag` call, the `_update_etag` method, and the unused `ETagManager` import from the HTTP replace branch | REQ-001; AC-1, AC-2 | `handle_existing_document` calls `self._update_etag(...)` at `:101` before returning `replace=True`; `ETagManager` import at `:13`; sole production call site of `ETagManager.update` (checked in Step 3) | `tests/rag/ingestion/test_ingestion_freshness.py` | Verified |
| `scripts/rag/ingestion/etag_manager.py` | Modify | Add `resolve_incoming` guarded value selection sharing the existing staleness/parse/exception semantics; `update()` delegates to the shared core with unchanged behavior | REQ-002; AC-4 | `update()` guard rules at `:31-55` (`ValueError` on empty `new_fetched_at` `:42-43`, both-`None` early return `:44-45`, `_is_stale_update` `:57-90` with `InvalidIncomingTimestampError`/`InvalidStoredTimestampError`) (checked in Step 3) | `tests/rag/ingestion/test_ingester_etag_guard.py` | Verified |
| `scripts/rag/ingestion/transaction_commit.py` | Modify | Resolve incoming vs. stored freshness inside `begin_immediate()` before the delete+insert on the replace branch; `insert` carries the resolved values | REQ-003; AC-2, AC-3 | Replace branch deletes then inserts with payload freshness unconditionally at `:59-78`; insert SQL carries `etag`, `last_modified`, `fetched_at` in `document_persistence.py:77-95` (checked in Step 3) | `tests/rag/ingestion/test_ingestion_freshness.py` | Verified |
| `tests/rag/ingestion/test_ingestion_freshness.py` | Modify | Add the failed-re-ingestion regression, transaction-abort atomicity, fresh/stale insert-semantics, and `resolve_incoming` unit tests | REQ-004; AC-1, AC-2, AC-3, AC-4 | File exists with `TestGetOrCreateDocumentFreshness` tests (`:149-254`) mixing real-`DocumentManager` and mock-based cases (re-verified this cycle); no test pins the pre-commit `_update_etag` call — `rg '_update_etag'` matches only `document_manager.py` (checked in Step 3) | itself | Verified |
| `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` | Modify | Update the existing-document-handling description of ETag refresh ordering to the commit-boundary design | REQ-005; AC-5 | Doc states "otherwise the ETag fields are refreshed and the chunks are replaced" at line 36 — describes the current pre-commit behavior (checked in Step 3) | N/A: documentation file, validated by review | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/document_persistence.py` | `get_or_create` delegates the skip/replace decision to `handle_existing_document`; `insert` is the freshness write target of REQ-003; its public signatures stay unchanged (see Design) | REQ-001, REQ-003 |
| `scripts/rag/ingestion/ingester.py` | Defines the call sequence `get_or_create` → `ChunkFactory.prepare` → `commit`, and the failure branch that skips commit when embedding fails (`:281-327`) | REQ-001, REQ-004 |
| `scripts/rag/ingestion/http_fetcher.py` | Shows how a wrong stored etag produces the permanent 304 skip; read-only (out of scope) | REQ-001 rationale |
| `tests/rag/ingestion/test_ingester_etag_guard.py` | Characterization suite pinning `ETagManager.update` guard behavior; must stay green and unchanged | REQ-002 |
| `tests/rag/ingestion/test_rag_ingester.py` and `tests/rag/ingestion/test_ingester.py` | Mock-based ingestion tests that call the changed classes; must stay green | REQ-001, REQ-003 |
| `tests/rag/ingestion/test_ingester.py` (real-sqlite `_FakeSQLiteHelper(conn)` harness, `:116`) | Reusable pattern for the REQ-004 integration tests against a real in-memory `documents`/`chunks` schema | REQ-004 |

## Acceptance Criteria
- AC-1 (REQ-001, REQ-004): After a failed re-ingestion (embedding or commit failure), the `documents` row still holds the previous `etag`/`last_modified`/`fetched_at`, and a subsequent run re-processes the URL (covered by a test).
- AC-2 (REQ-001, REQ-003): After a successful re-ingestion, the new freshness values land in the same transaction as the new chunks; no freshness write occurs outside it (covered by a test).
- AC-3 (REQ-003, REQ-004): A transaction abort leaves both `documents` and `chunks` at pre-run values (covered by a test).
- AC-4 (REQ-002, REQ-004): A stale incoming payload cannot regress stored freshness on the replace path; `resolve_incoming` guard rules match `update()`'s documented contract (covered by tests).
- AC-5 (REQ-005): `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` describes the commit-boundary ordering.
- AC-6 (REQ-001..005): `uv run pytest tests/rag/ingestion` passes and changed lines reach the `rules/toolchain.md` diff-cover threshold (≥ 90%).

## Tests
- REQ-004(a): Integration test on a real in-memory SQLite (`documents`/`chunks` schema, `_FakeSQLiteHelper(conn)` pattern): HTTP document with stored etag, payload with changed etag, embedding forced to fail → stored `etag`/`fetched_at` unchanged; second run with the same payload reaches the replace/commit path again (not freshness-skipped).
- REQ-004(b): Transaction-abort test (raise inside the commit's chunk-insert loop) → `documents` and `chunks` rows equal pre-run values.
- REQ-004(c)/(d): Insert-semantics tests: fresh payload → row carries payload freshness; stale payload (older `fetched_at`) → row carries stored freshness.
- REQ-004(e): `resolve_incoming` unit tests mirroring `test_ingester_etag_guard.py` guard cases (stale skip, both-`None` keep-stored, invalid timestamps raise, no-stored-row keeps-incoming).
- Characterization: `tests/rag/ingestion/test_ingester_etag_guard.py` stays unchanged and green (`ETagManager.update` observable behavior is preserved).

## Documentation Impact
`docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` line 36 currently describes the pre-commit refresh ("otherwise the ETag fields are refreshed and the chunks are replaced"); it must be updated to the commit-boundary design (REQ-005). `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` §4.9 describes `ETagManager`'s guard, which stays semantically correct; add the `resolve_incoming` selection mode only if the implementation changes the documented API surface.

## Assumptions
- Crawl/chunk payloads always carry a non-empty `fetched_at`; if one is empty, `resolve_incoming` raises `ValueError` inside the transaction → rollback → the URL fails the run with no partial freshness write (falsifiable by REQ-004 tests).
- No existing test asserts the pre-commit etag advancement (verified: `rg '_update_etag'` matches only `document_manager.py`; mock-based ingestion tests stub `handle_existing_document`) (checked in Step 3).
- `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` needs no row because `ETagManager`'s documented guard semantics are preserved unchanged.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Which production `documents` rows already carry an advanced etag with un-replaced chunks (rows damaged by this bug before the fix ships) | Live RAG DB inspection (`/opt/llm/db/rag.sqlite`), out of reach for this planning phase | Post-fix operational audit: compare `documents.fetched_at` against the newest registered chunk-file timestamps; force re-ingest (`--force`) the affected URLs | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Modify | Medium | 0 | High (single maintainer) | not applicable (rsynced) |
| `scripts/rag/ingestion/transaction_commit.py` | Modify | Medium | 0 | High (single maintainer) | not applicable (rsynced) |
| `scripts/rag/ingestion/etag_manager.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingestion_freshness.py` | Modify | Low | 0 | High (single maintainer) | not applicable (rsynced) |
| `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` | Modify | Low | 8 | High (single maintainer) | not applicable (rsynced) |

## Design
- Path B classification: the fix moves a DB write across module boundaries (`document_manager` → `etag_manager` → `transaction_commit`), adds a new guard API, and carries a docs update — multi-file coordination with a design decision, not a single-field change.
- Decision — guarded value selection at insert: resolve incoming-vs-stored inside the transaction before delete+insert. Rejected alternative (move the `_update_etag` UPDATE inside the transaction): the replace branch's insert already carries payload freshness and would overwrite the UPDATE anyway — the current guard demonstrably never affects the final stored row on a successful replace (verified in Step 2); only moving the decision to the insert values makes the guard real.
- Decision — behavior change on stale payloads: today a stale or `etag`/`last_modified`-less payload nulls/regresses the freshness columns via the insert after the guard skipped its UPDATE; after the fix the stored values are carried instead. This is the guard contract the issue requires ("preserve the stale-timestamp guard semantics after the move"); `test_ingester_etag_guard.py` already pins these rules for `update()`.
- Decision — keep `ETagManager.update`: its guard contract and characterization tests stay; after REQ-001 it has no production caller. Deleting it now would contradict the issue's "keep the guarded fast-forward" intent and delete its test home; removal is deferred to `rules/coding.md` Deprecation policy (next plan touching this file with a zero-caller `rg` re-check).
- Decision — keep `handle_existing_document`'s `fetched_at` parameter and `DocumentStore.get_or_create`'s pass-through: the parameter becomes unused after REQ-001, but removing it cascades into `ingester.py` and mock-based tests (`test_rag_ingester.py`), which the issue does not require (AGENTS.md rule 5: change only what the task requires). Ruff does not select `ARG`, so the unused parameter is lint-clean.
- Dependency graph (Step 3): `DocumentManager` importers — `document_persistence.py`, `ingester.py`, `transaction_commit.py`, 4 test files; `TransactionManager` importers — `ingester.py`, 2 test files; `ETagManager` importers — `document_manager.py`, `test_ingester_etag_guard.py`. Historical analysis: churn (30d) 0 for all three production files and the test file, 8 for the doc file; top author single-maintainer for all (checked in Step 3 via `git log --since=30.days`). Operational check: `fuser /opt/llm/db/rag.sqlite` returned no holders (checked in Step 3); `ss` N/A — no port involved. Persisted schema check: N/A — DML-only change, no DDL, schema version, or migration.
- `scan_change_consumers.py` not run: no persisted schema, public API, or shared constant changes; the import scan above enumerates every consumer.
- Validation quality baseline (Step 5): `radon cc` on the three production files — no C or worse grade; `vulture scripts/ --min-confidence 80` and `bandit -r scripts/ -c pyproject.toml` — no findings in the target files (pre-existing findings elsewhere out of scope); `pip-audit` N/A: no dependency upgrade planned. Diff-cover current number not measured in this cycle (no code change yet); the Plan's validation requires ≥ 90% on changed lines at implementation per `rules/toolchain.md`.

## Implementation steps
1. **Phase 1: Failing regression tests (RED)**
   - [ ] Add the failed-re-ingestion, transaction-abort, fresh/stale insert-semantics, and `resolve_incoming` tests to `tests/rag/ingestion/test_ingestion_freshness.py` using a real in-memory SQLite harness (REQ-004; must fail against current code before Phase 2)
2. **Phase 2: Commit-boundary fix (GREEN)**
   - [ ] Add `resolve_incoming` to `ETagManager` and delegate `update()`'s guard decision to the shared core (REQ-002; `scripts/rag/ingestion/etag_manager.py`) — minimal change only: guard rules, exceptions, and log behavior of `update()` stay identical
   - [ ] Resolve freshness inside `begin_immediate()` before delete+insert on the replace branch (REQ-003; `scripts/rag/ingestion/transaction_commit.py`)
   - [ ] Delete the `_update_etag` call, method, and `ETagManager` import from `handle_existing_document`'s replace branch (REQ-001; `scripts/rag/ingestion/document_manager.py`)
3. **Phase 3: Documentation & verification & deploy hand-off**
   - [ ] Update the ETag refresh-ordering description (REQ-005; `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`)
   - [ ] Run the `rules/toolchain.md` gate sequence on the touched files (pytest targeted + `tests/rag/ingestion`, ruff, mypy, lint-imports, bandit, diff-cover ≥ 90%) (REQ-001..004; `scripts/rag/ingestion/document_manager.py`, `scripts/rag/ingestion/etag_manager.py`, `scripts/rag/ingestion/transaction_commit.py`, `tests/rag/ingestion/test_ingestion_freshness.py`)
   - [ ] Deploy hand-off: after the change is committed and pushed, `scripts/` sync via `skills/deploy/SKILL.md` is the user's decision (approval gate) (REQ-001..003)

### Release units
**Unit**: etag-atomic-fix | **Phases**: 1, 2 | **Reason**: Phase 1 adds failing regression tests against the pre-commit write; the suite is green only after Phase 2's production fix, so neither phase validates alone.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/transaction_commit.py` | Integration | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -v` | Failed re-ingestion leaves stored freshness unchanged; success path writes freshness atomically with chunks |
| `scripts/rag/ingestion/etag_manager.py` | Unit | `uv run pytest tests/rag/ingestion/test_ingester_etag_guard.py tests/rag/ingestion/test_ingestion_freshness.py -v` | `update()` characterization tests unchanged; `resolve_incoming` guard rules verified |
| `scripts/rag/ingestion/document_manager.py` | Regression | `uv run pytest tests/rag/ingestion` | All ingestion tests green with no pre-commit etag write anywhere |
| `scripts/` touched files | Static gates | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll` | Clean, no new findings |
| changed lines | Coverage | `uv run coverage run -m pytest tests/` then `uv run coverage xml` and `uv run diff-cover coverage.xml --compare-branch=master` | ≥ 90% on changed lines |

## Risks
- **Risk**: mock-based ingestion tests (`test_rag_ingester.py`, `test_ingester.py`) stub `handle_existing_document` and cannot detect the behavior change → **Mitigation**: REQ-004 integration tests run the real `DocumentManager`/`TransactionManager` against an in-memory SQLite schema.
- **Risk**: stale/validator-less payloads now keep stored freshness instead of nulling the columns — a real behavior change on an edge case → **Mitigation**: pinned explicitly by REQ-004(d) tests and described in the REQ-005 doc update; recorded in Design.
- **Risk**: `resolve_incoming` divergence from `update()`'s guard rules would silently split the two paths → **Mitigation**: `update()` delegates to the same shared core; `test_ingester_etag_guard.py` stays unchanged as characterization coverage.
- **Risk**: rows already damaged by the bug keep serving stale chunks after deploy → **Mitigation**: UNK-01 resolution path — post-fix SQL audit and `--force` re-ingest of affected URLs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add failing regression tests in `tests/rag/ingestion/test_ingestion_freshness.py` | In Progress | — | — | REQ-004 |
| 2 | Commit-boundary fix in `scripts/rag/ingestion/etag_manager.py`, `scripts/rag/ingestion/transaction_commit.py`, `scripts/rag/ingestion/document_manager.py` | In Progress | — | — | REQ-001, REQ-002, REQ-003 |
| 3 | Docs update + gate sequence + deploy hand-off | In Progress | — | — | REQ-005, REQ-001..004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocker recorded at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| `implementations/20261106-114554_01_scripts_rag_ingestion_document_manager.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261106-114554_02_scripts_rag_ingestion_etag_manager.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261106-114554_03_scripts_rag_ingestion_transaction_commit.py.md` | 2 | Procedure | Pending | — | — |
| `implementations/20261106-114554_04_tests_rag_ingestion_test_ingestion_freshness.py.md` | 1 | Procedure | Pending | — | — |
| `implementations/20261106-114554_05_docs_21_rag_rag_02_05_ingestion_pipeline-document-manager.md.md` | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: `issues/20261106-073538_raging002_etag-updated-before-reingestion.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261106-094942
- **Related target files**: `scripts/rag/ingestion/document_manager.py`, `scripts/rag/ingestion/etag_manager.py`, `scripts/rag/ingestion/transaction_commit.py`, `tests/rag/ingestion/test_ingestion_freshness.py`, `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Required Changes bullet 1; `_update_etag` call verified at `document_manager.py:101` (checked in Step 2) | `scripts/rag/ingestion/document_manager.py` | Phase 2 | AC-1, AC-2 | Phase 1 regression tests | Confirmed by repository evidence |
| REQ-002 | Issue Constraints "Preserve the ETagManager stale-timestamp guard semantics"; guard rules verified at `etag_manager.py:31-90` (checked in Step 2) | `scripts/rag/ingestion/etag_manager.py` | Phase 2 | AC-4 | `test_ingester_etag_guard.py` characterization + `resolve_incoming` unit tests | Confirmed by repository evidence |
| REQ-003 | Issue Implementation Intent "defer the write to the same BEGIN IMMEDIATE transaction"; delete+insert verified at `transaction_commit.py:57-78` (checked in Step 2) | `scripts/rag/ingestion/transaction_commit.py` | Phase 2 | AC-2, AC-3 | Phase 1 integration tests | Confirmed by repository evidence |
| REQ-004 | Issue Testing Expectations | `tests/rag/ingestion/test_ingestion_freshness.py` | Phase 1 | AC-1, AC-2, AC-3, AC-4, AC-6 | New regression + unit tests | Explicit in issue |
| REQ-005 | Issue Documentation Impact; current wording verified at `rag_02_05_...md:36` (checked in Step 3) | `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` | Phase 3 | AC-5 | Review of the updated doc section | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261106-114554 -->