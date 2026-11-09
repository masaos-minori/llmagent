## Goal
- Stop re-embedding chunk groups that can never be committed: reject wrong-size embeddings and out-of-schema `chunk_type` values before the transaction, and quarantine a group that fails the commit with a deterministic integrity error to `failed/` with its reason, while errors that may be transient keep their files in place.

## Priority
Medium

## Scope
- **In-Scope**:
  - Embedding-size validation in `EmbeddingService.embed_and_store` using the existing `validate_embedding_blob` (expected dimension from `db.store_protocols`), returning an existing failure reason so the group is routed with `failed/`.
  - `chunk_type` validation in `read_chunk_json` (`scripts/rag/ingestion/pipeline_utils.py`): only `text` and `code`, matching the `chunks` CHECK constraint.
  - In `RagIngester.ingest_url_group`, `sqlite3.IntegrityError` from the commit routes the group to `failed/` (reason `STORAGE_FAILED`); every other `sqlite3.Error` keeps today's behavior.
  - Tests for a wrong-size vector, an empty and an unknown `chunk_type`, an integrity error, and a transient error; the ingester documentation.
- **Out-of-Scope**:
  - Consuming the retry directory, changing the embedding retry policy, a new retry mechanism, classifying `OperationalError` messages (see Design).
- **Dependencies**: N/A: none (history only: the archived `raging003` and `raging005` issues).

## Background
Review finding F-015 (Confidence Medium in the Issue). Verified facts (checked in Step 3): `EmbeddingService.get_embedding` returns any non-empty list without comparing its length (`scripts/rag/ingestion/embedding.py:40-69`), and `embed_and_store` builds the BLOB with `floats_to_blob` without validating it (L71-112), although `validate_embedding_blob` in `scripts/db/store_protocols.py:37-46` already checks the byte length against `get_embedding_dims()`. `read_chunk_json` accepts any string, including empty, for `chunk_type` (`_validate_str_or_empty`, `scripts/rag/ingestion/pipeline_utils.py:199`), and `embed_and_store` substitutes `""` for a missing value (`embedding.py:85`), while the schema enforces `CHECK (chunk_type IN ('text','code'))` (`scripts/db/schema_sql.py:45`); `ChunkSplitter` writes only `text` or `code` (`chunk_splitter.py:10`). `TransactionManager.commit` runs inside `begin_immediate()` (rolled back on error) and raises `sqlite3.Error` to `RagIngester._process_url_groups`, which logs it and records `unexpected_failure` without routing any file, so the chunk files stay in `chunk/` and the next run re-embeds the group. Reproduced in Step 3 against the installed `vec0.so`: a wrong-dimension insert raises `sqlite3.OperationalError: Dimension mismatch ...` (the same class used for lock and I/O errors), while a CHECK violation raises `sqlite3.IntegrityError`. Consequence: the dimension case cannot be classified by exception type at commit and must be caught by validation before the transaction; only `IntegrityError` is a safe deterministic signal at commit time. The Issue names `chunk_grouping.py` for `read_chunk_json`, but the function is defined in `pipeline_utils.py`.

## Problem
An embedding model change, a bad payload, or a schema-violating chunk produces a permanent per-run cost (one embedding call per chunk) and an ever-growing failure log.

## Reason for Change
The failure is deterministic, so retrying cannot help; the run should quarantine the group and report it.

## Implementation Intent
Validate early (read time for `chunk_type`, embed time for the vector size) so deterministic failures take the existing validation and routing path; add one narrow commit-time rule (`IntegrityError` means quarantine); leave every other database error retryable exactly as today.

## Requirements
- `REQ-001`: A chunk whose embedding BLOB length does not match the expected dimension is rejected in `embed_and_store` before any transaction, with an existing failure reason, and its group is routed to `failed/` with that reason.
- `REQ-002`: `read_chunk_json` rejects a `chunk_type` that is not `text` or `code` (including empty) with `ChunkFormatError`, so the group takes the existing `PARSE_FAILED` routing.
- `REQ-003`: A `sqlite3.IntegrityError` raised by `TransactionManager.commit` routes the whole group to `failed/` with reason `STORAGE_FAILED`, the database stays consistent (the transaction is rolled back), and the group is not retried on the next run.
- `REQ-004`: Any other `sqlite3.Error` (for example `OperationalError`) keeps its files in `chunk/` and keeps the current logging and `unexpected_failure` result.
- `REQ-005`: Transaction atomicity, the embedding retry policy, and the retry directory are unchanged.
- `REQ-006`: The ingester documentation states which failures are deterministic and routed to `failed/`.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/embedding.py` | Modify | Validate the embedding BLOB size with `validate_embedding_blob` and return a failure reason on mismatch | `REQ-001` / AC-1 | `embed_and_store` L71-112 builds the BLOB unchecked; `validate_embedding_blob` exists (checked in Step 3) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `scripts/rag/ingestion/pipeline_utils.py` | Modify | Restrict `chunk_type` to `text` / `code` in `read_chunk_json` | `REQ-002` / AC-2 | `_validate_str_or_empty(data, "chunk_type", "chunk")` at L199 (checked in Step 3) | `tests/rag/ingestion/test_pipeline_utils_strict.py` | Verified |
| `scripts/rag/ingestion/ingester.py` | Modify | Catch `sqlite3.IntegrityError` around the commit in `ingest_url_group` and route the group to `failed/` | `REQ-003`..`REQ-005` / AC-3..AC-5 | `tx_mgr.commit` at L331 with no local handler; outer handler only in `_process_url_groups` (checked in Step 3) | `tests/rag/ingestion/test_ingester.py` | Verified |
| `tests/rag/ingestion/test_ingester.py` | Modify | Wrong-size embedding, integrity-error quarantine, transient-error retention tests; update the existing `TestIntegrityErrorPropagation` group-level test to the new routing behavior | `REQ-001`, `REQ-003`, `REQ-004` / AC-1, AC-3, AC-4 | Existing ingester tests with stub embedding clients (checked in Step 3) | self | Verified |
| `tests/rag/ingestion/test_pipeline_utils_strict.py` | Modify | Empty and unknown `chunk_type` rejection tests; fix fixtures that rely on lenient values | `REQ-002` / AC-2 | Existing strict-reader tests; `CHUNK_PAYLOAD["chunk_type"] == "text"` (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` | Modify | Describe deterministic-failure routing near L104-110 | `REQ-006` / AC-6 | L104-110 list the `failed/` routing cases without these (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/db/store_protocols.py` | `validate_embedding_blob`, `get_embedding_dims`, `get_embedding_bytes` (L27-46) | `REQ-001` |
| `scripts/rag/ingestion/transaction_commit.py` | `begin_immediate()` rollback and the `INSERT` statements that raise (L58-122); unchanged | `REQ-003`, `REQ-005` |
| `scripts/rag/ingestion/file_routing.py` | `FileRouter.route` and `.error.json` writing | `REQ-003` |
| `scripts/rag/exceptions.py` | `IngestionFailureReason` values (`VALIDATION_FAILED`, `STORAGE_FAILED`, `PARSE_FAILED`) | `REQ-001`, `REQ-003` |
| `scripts/db/schema_sql.py` | `chunks.chunk_type` CHECK (L45) | `REQ-002` |
| `scripts/rag/ingestion/chunk_splitter.py` | Producer of `chunk_type` values (`text` / `code`) | `REQ-002` |

## Acceptance Criteria
- AC-1 (`REQ-001`): a stub embedding returning a wrong-length vector makes the group end in `failed/` with a reason, with no `commit` call, and a second run finds no file in `chunk/`.
- AC-2 (`REQ-002`): `read_chunk_json` raises `ChunkFormatError` for `chunk_type` `""`, `"chunk"`, and `"foo"` and accepts `"text"` and `"code"`.
- AC-3 (`REQ-003`): a forced `sqlite3.IntegrityError` from `commit` routes every file of the group to `failed/` with `STORAGE_FAILED`, the database has no partial rows for that URL, and the run continues with the next group.
- AC-4 (`REQ-004`): a forced `sqlite3.OperationalError` leaves the files in `chunk/` and the result is the existing `unexpected_failure`.
- AC-5 (`REQ-005`): existing atomicity, retry, and routing tests pass unmodified, with two fixture/test updates found in Step 3a of plan-to-implementation-procedure: (1) `test_integrity_error_routes_to_failed_via_ingest_url_group` in `tests/rag/ingestion/test_ingester.py` (L1289) asserts the legacy `IntegrityError`-propagation behavior with `pytest.raises` and must be updated to assert the new `failed/` routing; (2) `test_dimension_mismatch_on_retry` (L433) asserts success for an 8-dim vector and must be updated to expect `VALIDATION_FAILED`, and the `_DIM = 384` fake-embedding fixtures must be aligned to the `get_embedding_dims()` constant because `embed_and_store` now validates every stub vector.
- AC-6 (`REQ-006`): the doc names the deterministic cases; docs checkers pass.

## Tests
- `REQ-001`: stub embedding client returning a wrong-size vector.
- `REQ-002`: parametrized `chunk_type` values at `read_chunk_json`.
- `REQ-003`/`REQ-004`: `commit` patched to raise `IntegrityError` and `OperationalError`; a real-schema test with the `chunk_type` CHECK where feasible.
- `REQ-005`: existing suites unmodified.
- Static: `uv run ruff check`, `uv run mypy`; `uv run pytest tests/rag/ingestion -q`.

## Documentation Impact
Yes (`REQ-006`): `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` (located via `docs/00_index.md` RAG rows), failure behavior only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- A wrong-size embedding is a validation failure and reuses `IngestionFailureReason.VALIDATION_FAILED` (no new enum member), and the `.error.json` carries the human-readable size message.
- Chunk files with an empty or other `chunk_type` already fail at commit (CHECK), so rejecting them at read time changes no previously successful outcome; whether legacy files with such values exist on the host is `不明` (UNK-01).
- Overlap judgment (Step 8b): `scripts/rag/ingestion/embedding.py` and `ingester.py` are not targets of other Frozen Plans; `tests/rag/ingestion/test_ingester.py` is not shared with another Frozen Plan at freeze time.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether chunk files with empty or unknown `chunk_type` exist in the production `rag-src/chunk` directory | Production directory not inspected | Owner-side `rg -L` or a one-off scan before deploy; such files would be routed to `failed/` after the change (they fail every run today) | False |
| UNK-02 | Whether `OperationalError` cases other than a dimension mismatch are deterministic (for example a corrupt vec table) | No further reproduction | Kept retryable by design; revisit only with evidence | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/embedding.py` | Modify | Medium (every embedded chunk; `radon`: `embed_and_store` B (7)) | 0 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/pipeline_utils.py` | Modify | Medium (every chunk read; `read_chunk_json` B (7)) | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/ingestion/ingester.py` | Modify | Medium (ingest loop; `radon`: `ingest_url_group` C (18)) | 4 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_pipeline_utils_strict.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files; ingest failure routing is runtime-facing). Architecture: `embedding.py` gains an import of `db.store_protocols.validate_embedding_blob` (the ingestion package already depends on `db.*`, for example `document_manager.py` imports `db.helper`); `lint-imports` 6 contracts kept at plan time; no new cycle. Dependency graph: `read_chunk_json` is imported by `embedding.py`, `ingester.py`, `chunk_grouping.py`, and tests; `embed_and_store` is reached through `ChunkFactory.prepare`. Complexity: `ingest_url_group` is already C (18), so the commit handling goes into a small private method that returns the routed result, keeping the main function from growing.

Alternatives: (a) classify `OperationalError` by message text ("Dimension mismatch") at commit, rejected (brittle string matching, and sqlite-vec message text is not a contract); (b) catch every `sqlite3.Error` and quarantine, rejected (a transient lock would quarantine good groups); (c) a new `EMBEDDING_DIMENSION_MISMATCH` enum value, rejected as unnecessary surface for a single case. Chosen: early validation plus `IntegrityError`-only quarantine.

Persisted schema check: not applicable (no DDL; the existing CHECK is only mirrored by validation).

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Wrong-size embedding, integrity-error, and transient-error tests (`REQ-001`, `REQ-003`, `REQ-004`; `tests/rag/ingestion/test_ingester.py`)
   - [ ] `chunk_type` rejection tests and fixture review (`REQ-002`; `tests/rag/ingestion/test_pipeline_utils_strict.py`)
2. **Phase 2: Early validation**
   - [ ] Embedding BLOB size validation (`REQ-001`; `scripts/rag/ingestion/embedding.py`)
   - [ ] `chunk_type` restriction (`REQ-002`; `scripts/rag/ingestion/pipeline_utils.py`)
3. **Phase 3: Commit-time quarantine**
   - [ ] `IntegrityError` routing in `ingest_url_group` via a small helper (`REQ-003`..`REQ-005`; `scripts/rag/ingestion/ingester.py`)
4. **Phase 4: Documentation**
   - [ ] Deterministic-failure routing text (`REQ-006`; `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`)
5. **Phase 5: Deployment & Verification**
   - [ ] `uv run pytest tests/rag/ingestion -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision, with the UNK-01 directory check (all requirements; `scripts/rag/ingestion/ingester.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/embedding.py`, `ingester.py` | Unit (stub embedding, in-memory DB) | `uv run pytest tests/rag/ingestion/test_ingester.py -q` | new tests fail on HEAD, pass after |
| `scripts/rag/ingestion/pipeline_utils.py` | Unit | `uv run pytest tests/rag/ingestion/test_pipeline_utils_strict.py -q` | rejection cases pass |
| ingestion suites | Regression | `uv run pytest tests/rag/ingestion -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: legacy chunk files with an empty `chunk_type` are now routed to `failed/` on the first run → **Mitigation**: they already fail every run at the CHECK; UNK-01 directory check before deploy.
- **Risk**: an `IntegrityError` that is actually transient (rare, for example a concurrent writer inserting the same URL) quarantines a good group → **Mitigation**: the quarantine is in `failed/` with a reason and is recoverable by moving the files back; uniqueness races are prevented by `begin_immediate`.
- **Risk**: the expected dimension in `get_embedding_dims()` differs from the running model after a model change → **Mitigation**: that is the intended rejection; the failure log and `.error.json` name the sizes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | In Progress | — | — |  |
| 2 | Phase 2: early validation | In Progress | — | — |  |
| 3 | Phase 3: commit-time quarantine | In Progress | — | — |  |
| 4 | Phase 4: documentation | In Progress | — | — |  |
| 5 | Phase 5: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-232810_4_tests_rag_ingestion_test_ingester.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261109-232810_1_scripts_rag_ingestion_embedding.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-232810_2_scripts_rag_ingestion_pipeline_utils.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-232810_3_scripts_rag_ingestion_ingester.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261109-232810_6_docs_21_rag_rag_02_04_ingestion_pipeline-ingester.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131234_ragrev015_poison-chunk-groups-retried.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-170534
- **Related target files**: `scripts/rag/ingestion/embedding.py`, `scripts/rag/ingestion/pipeline_utils.py`, `scripts/rag/ingestion/ingester.py`, `tests/rag/ingestion/test_ingester.py`, `tests/rag/ingestion/test_pipeline_utils_strict.py`, `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `embedding.py:71-112` | `scripts/rag/ingestion/embedding.py` | Phase 2 | AC-1 | wrong-size embedding test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/ingestion/test_ingester.py` | Phase 1 | AC-1 | wrong-size embedding test | Explicit in issue |
| REQ-002 | Required Changes 2; `pipeline_utils.py:199` | `scripts/rag/ingestion/pipeline_utils.py` | Phase 2 | AC-2 | `chunk_type` rejection tests | Confirmed by repository evidence |
| REQ-002 | Testing Expectations | `tests/rag/ingestion/test_pipeline_utils_strict.py` | Phase 1 | AC-2 | `chunk_type` rejection tests | Explicit in issue |
| REQ-003 | Required Changes 3; reproduction (`IntegrityError`) | `scripts/rag/ingestion/ingester.py` | Phase 3 | AC-3 | integrity-error quarantine test | Confirmed by repository evidence |
| REQ-003 | Testing Expectations | `tests/rag/ingestion/test_ingester.py` | Phase 1 | AC-3 | integrity-error quarantine test | Explicit in issue |
| REQ-004 | Required Changes 3 (transient kept); reproduction (`OperationalError`) | `scripts/rag/ingestion/ingester.py` | Phase 3 | AC-4 | transient-error retention test | Confirmed by repository evidence |
| REQ-004 | Acceptance Criteria 2 | `tests/rag/ingestion/test_ingester.py` | Phase 1 | AC-4 | transient-error retention test | Explicit in issue |
| REQ-005 | Constraints | `scripts/rag/ingestion/ingester.py` | Phase 3 | AC-5 | existing atomicity and routing tests | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/21_rag/rag_02_04_ingestion_pipeline-ingester.md` | Phase 4 | AC-6 | docs gates | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-232810 -->