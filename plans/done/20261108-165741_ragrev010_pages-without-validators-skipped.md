## Goal
- Stop treating two absent HTTP validators as "unchanged": an existing page whose stored and incoming `etag` and `last_modified` are both `None` (or whose stored pair or incoming pair is entirely absent) must be re-ingested, using one absence rule shared by the HTTP and file branches, while pages with equal non-null validators are still skipped.

## Priority
High

## Scope
- **In-Scope**:
  - `DocumentManager.handle_existing_document` (HTTP branch) and the shared absence rule used by the file branch (`_is_file_unchanged`).
  - Unit tests for the HTTP branch (`None`/`None`, one-sided `None`, equal non-null) against the real `DocumentManager`, and a documentation update of the freshness rule.
- **Out-of-Scope**:
  - Crawler fetch logic and the conditional-request (304) behavior, the `file://` freshness rule itself (already guarded; only refactored to share the helper), a content-hash fallback for validator-less pages (needs storage; see Unknowns), changing `ETagManager`.
- **Dependencies**: N/A: none.

## Background
Review finding F-004. In the HTTP branch of `handle_existing_document` (`scripts/rag/ingestion/document_manager.py:97-98`), `if stored["etag"] == etag and stored["last_modified"] == last_modified: return existing_doc_id, True, False` treats `None == None` as equal, so a page with no validators is skipped forever after first ingestion. The file branch guards this: `_is_file_unchanged` returns `False` when either etag is `None` (L105-114). The caller path is `DocumentPersistence.get_or_create` (`scripts/rag/ingestion/document_persistence.py:61`). `documents` stores only `etag`, `last_modified`, `fetched_at` (`scripts/db/schema_sql.py:24-32`), no content hash; `file://` documents carry a SHA-256 in the `etag` column, written by the crawl persister (`crawl_persister.py:72-82`), and `http_fetcher.py:119-121` replays the stored `etag` as `If-None-Match`, so a synthetic hash stored in `etag` for HTTP pages would also be sent as a conditional header (a reason a hash fallback is not planned here). No existing test covers the HTTP branch with absent validators (the existing HTTP calls in `tests/rag/ingestion/test_ingestion_freshness.py:393-450` use non-null values). The doc line to correct is `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md:36`.

## Problem
Sites without validators (static hosts, some documentation generators) are crawled once and never updated in the corpus, even when their content changes.

## Reason for Change
The corpus silently goes stale for exactly the sources that give the crawler no other change signal.

## Implementation Intent
Define the rule once: validators prove "unchanged" only when at least one validator is present and the stored and incoming pairs are equal; any pair with both validators absent means "unknown", so the page is re-ingested. Express it as one small helper used by the HTTP branch and by `_is_file_unchanged` (whose stricter etag-only comparison for `file://` stays). No fallback signal is added in this plan: re-ingesting is the safe default, the Issue's constraint "avoid re-embedding when a content hash is available" is satisfied because no hash is available for HTTP pages today.

## Requirements
- `REQ-001`: For an existing HTTP document, stored `(None, None)` with incoming `(None, None)` yields `(skip=False, replace=True)`.
- `REQ-002`: Equal non-null validators (etag equal and last_modified equal, at least one non-null) still yield `(skip=True, replace=False)`; any differing pair, and one-sided `None`, yield `replace=True`.
- `REQ-003`: The HTTP and file branches use the same absence helper; the `file://` outcomes (etag-only comparison, `None` on either side means changed) are unchanged.
- `REQ-004`: The force path, the no-stored-row path, and the "no freshness write here" behavior (raging002) are unchanged.
- `REQ-005`: The documentation states the absence rule and that validator-less pages are re-ingested each run.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-09 (fallout): added tests/rag/ingestion/test_ingester.py — test_skips_already_registered_url ingests the default _ChunkSpec (etag and last_modified both None) twice and relies on the None/None skip; give that test non-null validators so it keeps proving the skip path

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Modify | Shared absence helper; HTTP branch no longer treats `None`/`None` as equal | `REQ-001`..`REQ-004` / AC-1..AC-4 | HTTP equality at L97-98; file guard at L105-114 (checked in Step 3) | `tests/rag/ingestion/test_ingestion_freshness.py` | Verified |
| `tests/rag/ingestion/test_ingestion_freshness.py` | Modify | HTTP-branch tests against the real `DocumentManager` using the file's existing `_make_freshness_db` / `_seed_document` helpers; `None`/`None`, one-sided, equal non-null, partial-validator cases | `REQ-001`..`REQ-004` / AC-1..AC-4 | Helpers at L331-370 and the HTTP calls at L393-450, no absent-validator case (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` | Modify | Correct the "other sources" freshness bullet (L36) and state the absence rule | `REQ-005` / AC-5 | L36 says a skip needs both validators equal, silent on absence (checked in Step 3) | docs gates | Verified |
| `tests/rag/ingestion/test_ingester.py` | Modify | test_skips_already_registered_url ingests the default _ChunkSpec (etag and last_modified both None) twice and relies on the None/None skip; give that test non-null validators so it keeps proving the skip path | REQ-004 / AC-4 | _ChunkSpec defaults etag=None, last_modified=None (test_ingester.py:128-129); test_skips_already_registered_url at L551-586 (checked in Step 3a) | self | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/ingestion/document_persistence.py` | Sole caller of `handle_existing_document` (L61) | `REQ-001` |
| `scripts/rag/ingestion/etag_manager.py` | `update` / `resolve_incoming` keep stored values when incoming is both-`None`; unchanged | `REQ-004` |
| `scripts/rag/ingestion/http_fetcher.py` | Replays stored validators as conditional headers (L79-121) | Scope |
| `scripts/db/schema_sql.py` | `documents` columns (no content hash) | Scope |
| `docs/21_rag/rag_05_06-local-file-re-ingestion.md` | Describes the `file://` SHA-256 rule; must remain consistent | `REQ-003` |

## Acceptance Criteria
- AC-1 (`REQ-001`): a stored `(None, None)` row with an incoming `(None, None)` payload returns `(skip=False, replace=True)`.
- AC-2 (`REQ-002`): stored `("e", "lm")` with incoming `("e", "lm")` returns `(True, False)`; `("e", None)` against `("e", None)` returns `(True, False)`; a differing etag or last_modified, and `("e", "lm")` against `(None, None)` or the reverse, return `(False, True)`.
- AC-3 (`REQ-003`): the existing `TestIsFileUnchanged`-style tests (`test_ingestion_freshness.py:31-60`) pass unmodified; `file://` skip and replace outcomes are unchanged.
- AC-4 (`REQ-004`): `force=True`, missing stored row, and the freshness-atomicity tests (`L393-450`) pass unmodified.
- AC-5 (`REQ-005`): the doc names the absence rule; docs checkers pass.

## Tests
- `REQ-001`/`REQ-002`: parametrized HTTP-branch matrix against the real `DocumentManager` and an in-memory DB.
- `REQ-003`: existing file-guard tests unmodified, plus one test that both branches call the shared helper's rule.
- `REQ-004`: existing atomicity and force tests unmodified.
- Static: `uv run ruff check`, `uv run mypy`; `uv run pytest tests/rag -q`.

## Documentation Impact
Yes (`REQ-005`): `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` (located via `docs/00_index.md` RAG rows), intent and failure behavior only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- Re-ingesting validator-less pages on every crawl run is acceptable as the default (embedding cost scales with the number of such pages); the Issue's constraint on content hashing is read as applying only where a hash exists. A cheaper rule needs a storage decision and is a separate Plan (UNK-01).
- `etag`/`last_modified` of an HTTP document are `None` only when the server sent no such header; `ETagManager` never overwrites stored values with `None` (so a server that stops sending validators does not erase stored ones, and the stored-present/incoming-absent case already re-ingests).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Acceptable fallback signal for validator-less pages: always re-ingest (this Plan) versus a stored content hash (new column or reuse of `etag`, with the `If-None-Match` replay side effect) | Owner decision on embedding cost versus a schema or header change | Owner decides before or during implementation; this Plan implements always re-ingest, and a hash fallback would be a new Plan (persisted-schema change) | False |
| UNK-02 | How many validator-less pages exist in the production corpus (cost of the default) | Corpus statistics | Owner-side query of `documents WHERE etag IS NULL AND last_modified IS NULL` after deploy | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Modify | Medium (decides skip or re-ingest for every existing document; one caller) | 2 | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingestion_freshness.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/ingestion/test_ingester.py` | Modify | Not assessed (amendment 2026-11-09) | N/A | N/A | Not assessed (amendment 2026-11-09) |

## Design
Path A (3 target files, no interface or schema change; `handle_existing_document` keeps its signature and return meaning). Complexity: `handle_existing_document` B (8) and `_is_file_unchanged` A (3); the shared helper keeps both at or below B.

Alternatives: (a) content-hash comparison: rejected here (no storage for it, and reusing `etag` would be replayed as `If-None-Match`); (b) a schema column for a hash: rejected as a persisted-schema change beyond this fix (UNK-01). Chosen: absence means unknown, re-ingest, with one shared helper.

Validation baseline: `radon cc` recorded above; `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: no changed lines at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] HTTP-branch matrix with the real `DocumentManager` (`REQ-001`..`REQ-004`; `tests/rag/ingestion/test_ingestion_freshness.py`)
   - [ ] Modify (REQ-004; `tests/rag/ingestion/test_ingester.py`) — amendment 2026-11-09
2. **Phase 2: Shared absence rule**
   - [ ] Helper plus HTTP branch and `_is_file_unchanged` rewiring (`REQ-001`..`REQ-004`; `scripts/rag/ingestion/document_manager.py`)
3. **Phase 3: Documentation**
   - [ ] State the absence rule (`REQ-005`; `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] `uv run pytest tests/rag -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/ingestion/document_manager.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Unit (real manager, in-memory DB) | `uv run pytest tests/rag/ingestion/test_ingestion_freshness.py -q` | new `None`/`None` test fails on HEAD, passes after |
| ingestion suites | Regression | `uv run pytest tests/rag/ingestion -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: validator-less pages are re-chunked and re-embedded every run → **Mitigation**: stated in Assumptions and UNK-02; the rule is one function, and a hash fallback can replace it later without touching callers.
- **Risk**: a transient absence of validators (server config change) triggers one extra re-ingest → **Mitigation**: harmless; stored values are not erased by `ETagManager`.
- **Risk**: the shared helper changes `file://` behavior → **Mitigation**: the file branch keeps its etag-only comparison and its tests run unmodified (AC-3).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | Completed | — | 20261109-182406 | Proc 01 (test_ingestion_freshness.py) and proc 04 (test_ingester.py) archived; skip path adversarially verified |
| 2 | Phase 2: shared absence rule | Completed | — | 20261109-182406 | Proc 01 (document_manager.py) archived; ruff/mypy/lint-imports/bandit clean |
| 3 | Phase 3: documentation | Completed | — | 20261109-182406 | Proc 03 (rag_02_05-ingestion_pipeline-document-manager.md) archived; docs gates pass |
| 4 | Phase 4: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-142759_01_scripts_rag_ingestion_document_manager.py.md | 1, 2 | Procedure | Completed | — | — |
| implementations/20261109-142759_03_docs_21_rag_rag_02_05_ingestion_pipeline-document-manager.md.md | 3 | Procedure | Completed | — | — |
| implementations/20261109-142759_04_tests_rag_ingestion_test_ingester.py.md | 1 | Procedure | Completed | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131124_ragrev010_pages-without-validators-skipped.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-165741
- **Related target files**: `scripts/rag/ingestion/document_manager.py`, `tests/rag/ingestion/test_ingestion_freshness.py`, `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`, `tests/rag/ingestion/test_ingester.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `document_manager.py:97-98` | `scripts/rag/ingestion/document_manager.py` | Phase 2 | AC-1 | HTTP `None`/`None` test | Confirmed by repository evidence |
| REQ-001 | Required Changes 3 | `tests/rag/ingestion/test_ingestion_freshness.py` | Phase 1 | AC-1 | HTTP `None`/`None` test | Explicit in issue |
| REQ-002 | Acceptance Criteria 2 | `scripts/rag/ingestion/document_manager.py` | Phase 2 | AC-2 | HTTP matrix | Explicit in issue |
| REQ-002 | Required Changes 3 | `tests/rag/ingestion/test_ingestion_freshness.py` | Phase 1 | AC-2 | HTTP matrix | Explicit in issue |
| REQ-003 | Acceptance Criteria 3 | `scripts/rag/ingestion/document_manager.py` | Phase 2 | AC-3 | existing file-guard tests | Explicit in issue |
| REQ-004 | Constraints | `scripts/rag/ingestion/document_manager.py` | Phase 2 | AC-4 | atomicity and force tests | Explicit in issue |
| REQ-004 | Constraints | `tests/rag/ingestion/test_ingestion_freshness.py` | Phase 1 | AC-4 | atomicity and force tests | Explicit in issue |
| REQ-005 | Documentation Impact; doc L36 | `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md` | Phase 3 | AC-5 | docs gates | Confirmed by repository evidence |
| REQ-004 | Amendment 2026-11-09: test_skips_already_registered_url ingests the default _ChunkSpec (etag and last_modified both None) twice and relies on the None/None skip; give that test non-null validators so it keeps proving the skip path | tests/rag/ingestion/test_ingester.py | Phase 1 | AC-4 | self | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-142759 -->
