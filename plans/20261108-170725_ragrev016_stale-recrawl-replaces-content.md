## Goal
- Make document content and its freshness metadata always describe the same generation: when an HTTP chunk generation older than the stored one reaches `TransactionManager.commit`, skip the whole replacement (no delete, no insert) and report the skip, and when content is replaced under `--force` or for a `file://` source, persist the incoming metadata together with the incoming chunks so a restored older file cannot loop.

## Priority
Medium

## Scope
- **In-Scope**:
  - A public staleness query on `ETagManager` and a skip outcome in `TransactionManager.commit` (existing `(doc_id, skip, replace)` return contract) for a stale non-forced HTTP payload.
  - `RagIngester.ingest_url_group` reads the commit outcome: a stale skip is logged, the chunk files are routed like the existing "already registered" skip, and the result is a skip (not a success count).
  - Metadata written with replaced content is the incoming metadata for `file://` sources and for `force`, instead of the stored values.
  - Tests (stale HTTP, older-mtime file, force) and the ETagManager documentation.
- **Out-of-Scope**:
  - Redesigning freshness comparison, the both-`None` validator rule (see Unknowns), the HTTP skip decision in `DocumentManager` (`plans/20261108-165741_ragrev010_pages-without-validators-skipped.md`).
- **Dependencies**: Fix order against the sibling ingest plan:
  - **Depends on**: plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md | phase 3 | both edit the `tx_mgr.commit(...)` block in `RagIngester.ingest_url_group`; land the commit-error handling first so the skip handling is added to the settled block.

## Background
Review finding F-016 (control flow Explicit in code; the end-to-end scenarios are not reproduced). In the replace branch of `TransactionManager.commit` (`scripts/rag/ingestion/transaction_commit.py:58-85`) `ETagManager.resolve_incoming` returns the stored etag, last-modified, and `fetched_at` when the incoming payload is older (`etag_manager.py:59-81`, `_incoming_decision` L83-98), yet `delete_existing_document` and the chunk inserts run unconditionally, so the document row keeps the newer generation's metadata while its chunks come from the older one. Verified while reading (checked in Step 3): (1) the stale decision is based on `fetched_at` only; for `file://` documents `fetched_at` is the file mtime and `etag` is the SHA-256 (`crawl_persister.py:70-82`), so a restored older file has a different hash (replace is decided) but an older mtime (stale), the stored hash stays old, and the next run replaces again indefinitely; (2) a stale payload reaches `commit` in these ways: `force=True` skips the freshness decision (`document_manager.py:65-66`), a restored older `file://` file, or a manual re-queue of old chunk files; the normal run orders groups ascending by `(url, fetched_at)` (`ingester.py:_process_url_groups`), so ordinary HTTP re-crawls do not produce a stale payload; (3) `ingest_url_group` ignores `commit`'s return value (`ingester.py:331-345`), so a skip would currently be counted as a success; (4) the existing test `test_stale_payload_cannot_regress_stored_freshness` (`tests/rag/ingestion/test_ingestion_freshness.py:513-543`) asserts only the stored freshness and does not look at the chunks, so it passes under the new rule and is extended, not changed.

## Problem
Older content can overwrite newer content while the row keeps the newer validators, so later crawls skip the page (HTTP) or re-ingest forever (file).

## Reason for Change
Content and freshness metadata must describe the same generation; the guard protects only the metadata columns.

## Implementation Intent
Treat staleness as a decision about the whole replacement, made before any delete: for HTTP documents without `force`, a stale incoming generation is skipped. For `file://` (the file system is the source of truth, content hash is the change signal) and for `force` (an explicit operator request), the incoming generation always wins and its metadata is persisted with it. The both-`None` validator behavior of `resolve_incoming` stays as is.

## Requirements
- `REQ-001`: A stale non-forced HTTP incoming generation leaves the document row and its chunks (including `chunks_vec`) unchanged; `commit` returns the skip outcome without deleting or inserting.
- `REQ-002`: For `file://` sources and for `force=True`, replaced content is stored with the incoming `etag`, `last_modified`, and `fetched_at`; a restored older file is re-ingested once and then recognized as unchanged on the next run (no endless loop).
- `REQ-003`: `ingest_url_group` treats the skip outcome as a skip: it logs a distinct warning, routes the chunk files like the existing already-registered skip, and returns a skip result with `n_success = 0`.
- `REQ-004`: The single-transaction guarantee and the raging002 freshness-in-transaction behavior are unchanged for fresh payloads and for the both-`None` case.
- `REQ-005`: The ETagManager documentation states the stale-skip rule and the file/force exceptions.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/etag_manager.py` | Modify | Public staleness query built on `_incoming_decision`; no behavior change to `resolve_incoming` | `REQ-001`, `REQ-004` / AC-1, AC-4 | `_incoming_decision` returns `False` for stale, `None` for both-`None` (L83-98) (checked in Step 3) | `tests/rag/ingestion/test_ingestion_freshness.py` | Verified |
| `scripts/rag/ingestion/transaction_commit.py` | Modify | Skip the replace branch for a stale non-forced HTTP payload; incoming metadata for `file://` and `force` | `REQ-001`, `REQ-002`, `REQ-004` / AC-1, AC-2, AC-4 | `resolve_incoming` then `delete_existing_document` and inserts unconditionally (L58-85) (checked in Step 3) | `tests/rag/ingestion/test_ingestion_freshness.py` | Verified |
| `scripts/rag/ingestion/ingester.py` | Modify | Read `commit`'s outcome in `ingest_url_group`; skip handling and routing | `REQ-003` / AC-3 | Return value ignored at L331-345 (checked in Step 3) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `tests/rag/ingestion/test_ingestion_freshness.py` | Modify | Stale HTTP skip (chunks and `chunks_vec` unchanged), older-mtime file, force cases; extend the existing stale test | `REQ-001`, `REQ-002`, `REQ-004` / AC-1, AC-2, AC-4 | `TestFreshnessAtomicity` and `TestResolveIncomingGuard` with `_make_freshness_db` / `_seed_document` helpers (L331-570) (checked in Step 3) | self | Verified |
| `tests/rag/ingestion/test_ingester.py` | Modify | `ingest_url_group` skip-routing test with a stale payload | `REQ-003` / AC-3 | Existing ingester tests with stub services (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` | Modify | Section 4.9 ETagManager: stale payload skips the replace; file and force exceptions | `REQ-005` / AC-5 | Section 4.9 says stale input keeps stored values, silent on chunks (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | `handle_existing_document` (replace decision incl. `force`, `file://`); unchanged | `REQ-002` |
| `scripts/rag/ingestion/document_persistence.py` | `get_or_create` and the `file://` predicate | `REQ-002` |
| `scripts/rag/ingestion/crawl_persister.py` | `file://` payload (`etag` = SHA-256, `fetched_at` = mtime) | `REQ-002` |
| `tests/rag/ingestion/test_ingester_etag_guard.py` | Existing guard tests mirrored by `TestResolveIncomingGuard`; must stay green | `REQ-004` |

## Acceptance Criteria
- AC-1 (`REQ-001`): a stale HTTP payload committed with `replace=True`, `force=False` leaves `documents` and `chunks` and `chunks_vec` byte-identical and `commit` returns the skip outcome.
- AC-2 (`REQ-002`): an older-mtime `file://` payload with a different hash replaces the chunks and stores the incoming hash and mtime; running the same payload through `handle_existing_document` again yields skip; a stale payload with `force=True` replaces content and stores incoming metadata.
- AC-3 (`REQ-003`): a stale-skip run routes the files to the registered directory, logs the stale warning, and returns a skip result (not counted as success).
- AC-4 (`REQ-004`): fresh-payload, both-`None`, no-stored-row, atomicity, and `test_ingester_etag_guard.py` tests pass unmodified.
- AC-5 (`REQ-005`): the doc states the rule; docs checkers pass.

## Tests
- `REQ-001`: stale HTTP commit with chunk and vec row assertions.
- `REQ-002`: older-mtime file commit then re-check via `handle_existing_document`; force-stale commit.
- `REQ-003`: ingester-level skip routing.
- `REQ-004`: existing freshness and guard suites unmodified.
- Static: `uv run ruff check`, `uv run mypy`; `uv run pytest tests/rag/ingestion -q`.

## Documentation Impact
Yes (`REQ-005`): `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` section 4.9 (located via `docs/00_index.md` RAG rows), failure behavior only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- For `file://` sources the content hash, not the mtime, is the authoritative change signal (the existing file rule already compares only the hash), so an older mtime must not block replacement.
- `force=True` means the operator wants the incoming generation regardless of freshness; the stale guard therefore does not apply under `force`.
- Overlap judgment (Step 8b): `scripts/rag/ingestion/ingester.py` is also a target of `plans/20261108-170534_ragrev015_poison-chunk-groups-retried.md` (sequencing dependency recorded in Scope: ragrev015 first, because both edit the `commit` call block); `tests/rag/ingestion/test_ingestion_freshness.py` is also a target of `plans/20261108-165741_ragrev010_pages-without-validators-skipped.md` and `tests/rag/ingestion/test_ingester.py` of the ragrev015 plan; judged compatible (new test classes and cases in different areas of the files).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | How often a stale payload reaches `commit` in production | Production logs not inspected | The new stale-skip warning makes occurrences visible after deploy | False |
| UNK-02 | For both-`None` validator payloads `resolve_incoming` keeps the stored `fetched_at`, so after the ragrev010 change (validator-less pages re-ingested each run) `fetched_at` does not advance although content was replaced | Intended semantics of `fetched_at` for validator-less pages | Not changed here (Out-of-Scope); candidate follow-up Issue; harmless to the stale guard because stored `fetched_at` only moves forward when validators exist | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/etag_manager.py` | Modify | Low (additive query) | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/transaction_commit.py` | Modify | High (the only write path of ingested content; `radon`: `commit` B (7)) | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/ingester.py` | Modify | Medium (result handling in `ingest_url_group`, `radon` C (18)) | 4 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingestion_freshness.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files; ingest write-path behavior). Architecture: `transaction_commit` already imports `ETagManager` and `DocumentManager`; no new import edges; `lint-imports` 6 contracts kept at plan time. Dependency graph: `TransactionManager.commit` has one production caller (`ingester.py:331`) and test callers in `test_ingestion_freshness.py`; `resolve_incoming` is used only by `commit` and the guard tests. Complexity: `commit` B (7) and `ingest_url_group` C (18); the skip handling is a small private method in the ingester and the staleness rule a small helper in the commit module so neither function grows past its band.

Alternatives: (a) keep replacing but write incoming metadata always, rejected (older content would still overwrite newer content and regress validators); (b) make `resolve_incoming` itself raise on stale, rejected (it is also the contract for metadata-only callers). Chosen: whole-replacement skip for HTTP stale, incoming-wins for `file://` and `force`.

Persisted schema check: not applicable (no DDL or version change).

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Stale HTTP, older-mtime file, and force tests; extend the existing stale test (`REQ-001`, `REQ-002`, `REQ-004`; `tests/rag/ingestion/test_ingestion_freshness.py`)
   - [ ] Ingester skip-routing test (`REQ-003`; `tests/rag/ingestion/test_ingester.py`)
2. **Phase 2: Staleness query and commit rule**
   - [ ] Public staleness query (`REQ-001`, `REQ-004`; `scripts/rag/ingestion/etag_manager.py`)
   - [ ] Skip outcome and incoming-metadata rule (`REQ-001`, `REQ-002`, `REQ-004`; `scripts/rag/ingestion/transaction_commit.py`)
3. **Phase 3: Ingester handling**
   - [ ] Read the outcome, log, route, return a skip result (`REQ-003`; `scripts/rag/ingestion/ingester.py`)
4. **Phase 4: Documentation**
   - [ ] State the stale-skip rule (`REQ-005`; `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] `uv run pytest tests/rag/ingestion -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/ingestion/transaction_commit.py`)

### Release units
**Unit**: ragrev016-core | **Phases**: 2, 3 | **Reason**: a skip outcome from `commit` without the ingester handling would be counted as a success and routed as ingested.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/transaction_commit.py`, `etag_manager.py` | Unit (in-memory DB, real helpers) | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py tests/rag/ingestion/test_ingester_etag_guard.py -q` | new tests fail on HEAD, pass after |
| `scripts/rag/ingestion/ingester.py` | Unit | `uv run pytest tests/rag/ingestion/test_ingester.py -q` | skip routing asserted |
| ingestion suites | Regression | `uv run pytest tests/rag/ingestion -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: skipping a stale HTTP generation drops chunk files whose content the operator wanted → **Mitigation**: `force` bypasses the guard; the skip is logged distinctly; files are moved to the registered directory, not deleted.
- **Risk**: `file://` incoming-wins re-ingests an older file once, costing embeddings → **Mitigation**: one-time per restore; the next run sees the equal hash and skips.
- **Risk**: changing which metadata is written under `force` alters tests that assume stored values → **Mitigation**: the existing guard tests cover `resolve_incoming` directly and stay unmodified; only the commit-level behavior changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | Pending | — | — | |
| 2 | Phase 2: staleness query and commit rule | Pending | — | — | |
| 3 | Phase 3: ingester handling | Pending | — | — | |
| 4 | Phase 4: documentation | Pending | — | — | |
| 5 | Phase 5: deployment and verification | Pending | — | — | |

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
- **Source issue**: issues/20261108-131235_ragrev016_stale-recrawl-replaces-content.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-170725
- **Related target files**: `scripts/rag/ingestion/etag_manager.py`, `scripts/rag/ingestion/transaction_commit.py`, `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_ingestion_freshness.py`, `tests/rag/ingestion/test_ingester.py`, `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `transaction_commit.py:58-85` | `scripts/rag/ingestion/etag_manager.py` | Phase 2 | AC-1 | stale HTTP commit test | Confirmed by repository evidence |
| REQ-001 | Required Changes 1 | `scripts/rag/ingestion/transaction_commit.py` | Phase 2 | AC-1 | stale HTTP commit test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/ingestion/test_ingestion_freshness.py` | Phase 1 | AC-1 | stale HTTP commit test | Explicit in issue |
| REQ-002 | Required Changes 2; Acceptance Criteria 2 | `scripts/rag/ingestion/transaction_commit.py` | Phase 2 | AC-2 | older-mtime file and force tests | Derived from confirmed evidence |
| REQ-002 | Testing Expectations | `tests/rag/ingestion/test_ingestion_freshness.py` | Phase 1 | AC-2 | older-mtime file and force tests | Explicit in issue |
| REQ-003 | Required Changes 1 (route the chunk files); `ingester.py:331-345` | `scripts/rag/ingestion/ingester.py` | Phase 3 | AC-3 | ingester skip-routing test | Confirmed by repository evidence |
| REQ-003 | Required Changes 1 | `tests/rag/ingestion/test_ingester.py` | Phase 1 | AC-3 | ingester skip-routing test | Explicit in issue |
| REQ-004 | Constraints | `scripts/rag/ingestion/etag_manager.py` | Phase 2 | AC-4 | existing freshness and guard suites | Explicit in issue |
| REQ-004 | Constraints | `scripts/rag/ingestion/transaction_commit.py` | Phase 2 | AC-4 | existing freshness and guard suites | Explicit in issue |
| REQ-004 | Constraints | `tests/rag/ingestion/test_ingestion_freshness.py` | Phase 1 | AC-4 | existing freshness and guard suites | Explicit in issue |
| REQ-005 | Documentation Impact | `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` | Phase 4 | AC-5 | docs gates | Explicit in issue |
