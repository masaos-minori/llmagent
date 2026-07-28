## Goal

Fix `DocumentManager._update_etag` so it threads the real `existing_doc_id` through to `ETagManager` instead of a hardcoded `0`, so the ETag/Last-Modified refresh SQL on the "skip and refresh ETag" path actually updates the correct `documents` row.

## Scope

**In-Scope:**
- `scripts/rag/ingestion/document_manager.py:94-101` — add a `doc_id: int` parameter to `_update_etag` and pass it into `ETagManager(self._db, doc_id)` instead of the literal `0`
- `scripts/rag/ingestion/document_manager.py:61` — update the call in `handle_existing_document` to pass `existing_doc_id` through to `_update_etag`
- A new/extended unit test asserting the correct `doc_id` row (not `doc_id=0`) is updated on the skip path

**Out-of-Scope:**
- Any change to `scripts/rag/ingestion/etag_manager.py` (its SQL, staleness-guard, and null-fill logic remain unchanged)
- Any change to `_handle_existing_file` / the `file://` path (already receives and uses `existing_doc_id` correctly)
- Any change to `ingester.py:374`'s call to `handle_existing_document` (its public signature is unchanged)
- Documentation updates to `docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`, `docs/03_rag_02_05_ingestion_pipeline-document-manager.md`, or `docs/00_governance_07_needs-confirmation-inventory.md` (deferred to a later documentation-update phase)
- Any refactor of `ETagManager`'s constructor signature or the log message in `_log_updated`

## Assumptions

1. `ETagManager(self._db, 0)` at `document_manager.py:101` is an unintentional bug, not a deliberate design choice — confirmed by there being no test or comment justifying `doc_id=0`.
2. `existing_doc_id` is always a valid, already-inserted `documents.doc_id` (an autoincrement PK ≥ 1) at the point `handle_existing_document` is called.
3. No caller outside `scripts/` constructs `ETagManager` directly with a relied-upon `doc_id=0`.
4. Changing `_update_etag`'s signature is safe because it is a private (`_`-prefixed) method with exactly one call site (`document_manager.py:61`), both in the same file/class.

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether any other call site constructs `ETagManager` or calls `_update_etag`/`handle_existing_document` relying on `doc_id=0` | Resolved via grep: only `document_manager.py:101` constructs `ETagManager(`, only `document_manager.py:61,94` calls `_update_etag(`, only `ingester.py:374` calls `handle_existing_document(` | False |
| UNK-02 | Whether any existing test asserts the current `doc_id=0` behavior as intentional | Resolved: inspected `tests/test_ingester_etag_guard.py` — constructs `ETagManager(db, doc_id)` directly with explicit `doc_id=42`; other tests mock `handle_existing_document` entirely | False |
| UNK-03 | Whether `existing_doc_id` can ever be `0` or falsy in a way that a naive truthiness check would misroute | Resolved: `documents.doc_id` is declared `INTEGER PRIMARY KEY` (alias for SQLite `rowid`), starts at 1, never 0 | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/rag/ingestion/document_manager.py` — modify `_update_etag` signature and its call site in `handle_existing_document`
  - `tests/test_ingester_etag_guard.py` or a new test file — add/extend a test proving the correct `doc_id` is updated
- **Blast Radius:** Small — only internal wiring changes, no public interface change, no schema change. `ingester.py:365-383` calls `handle_existing_document` whose public signature is unchanged.
- **Risk Metrics:** Moderate churn (10 commits in history); existing test coverage via multiple test modules; Path A ("Small Task") criteria met.
- **Deploy Impact:** Existing — no `deploy/deploy.sh` changes needed.

## Implementation Steps

1. **Phase 1: Preparation / Analysis**
   - Re-run `grep -rn "ETagManager(" scripts/` and `grep -rn "_update_etag(" scripts/` immediately before coding to re-confirm no new call site was introduced.
   - Re-read `tests/test_ingester_etag_guard.py` in full to confirm the exact fixture/helper style (`_make_etag_mgr`) to follow.

2. **Phase 2: Core Logic Implementation**
   - Change `DocumentManager._update_etag` (lines 94-101) to accept `doc_id: int` as its first parameter and construct `ETagManager(self._db, doc_id)` instead of `ETagManager(self._db, 0)`.
   - Update the call site in `handle_existing_document` (line 61) to `self._update_etag(existing_doc_id, etag, last_modified, fetched_at)`, keeping argument order consistent with the method's existing style.
   - Add or extend a unit test that inserts a document row with a known non-zero `doc_id`, calls `DocumentManager.handle_existing_document(...)` with `force=False` and a non-`file://` URL plus new `etag`/`last_modified`/`fetched_at`, then asserts the `documents` row for that specific `doc_id` (not `doc_id=0`) was updated.
   - Run `uv run ruff check scripts/rag/ingestion/document_manager.py` and `uv run mypy scripts/rag/ingestion/document_manager.py` to confirm no new lint/type issues.

3. **Phase 3: Deployment & Verification**
   - Run the full targeted test set: `uv run pytest tests/test_ingester_etag_guard.py tests/test_ingestion_freshness.py tests/test_rag_ingester.py tests/test_rag_ingester_callback.py tests/test_rag_ingestion_pipeline.py -q`
   - Run `uv run pytest -q` (full suite) to catch any unforeseen regressions elsewhere.
   - No deploy step required — confirm this remains true after the diff is final.
   - Defer documentation updates to a later phase.

## Validation Plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/rag/ingestion/document_manager.py` | Unit — new/extended test for `handle_existing_document` skip path with a real (non-zero) `doc_id` | `uv run pytest tests/test_ingester_etag_guard.py -q` | New test passes; asserts the correct `doc_id` row was updated, not `doc_id=0` |
| `scripts/rag/ingestion/etag_manager.py` (regression-only) | Unit — existing direct `ETagManager` tests | `uv run pytest tests/test_ingester_etag_guard.py -q` | All existing tests pass unchanged |
| `scripts/rag/ingestion/ingester.py` (integration surface) | Integration — existing tests that mock `handle_existing_document` | `uv run pytest tests/test_ingestion_freshness.py tests/test_rag_ingester.py tests/test_rag_ingester_callback.py tests/test_rag_ingestion_pipeline.py -q` | All existing tests pass unchanged |
| Whole repo | Regression sweep | `uv run pytest -q` | No new failures |
| Static checks | Lint + type | `uv run ruff check scripts/rag/ingestion/document_manager.py` and `uv run mypy scripts/rag/ingestion/document_manager.py` | 0 errors |

## Risks

- The new `doc_id` parameter's position in `_update_etag`'s signature could be added inconsistently with `ETagManager.__init__`'s `(db, doc_id)` ordering, causing a silent argument-order bug → Mitigation: Add the parameter as the explicit first positional argument mirroring `ETagManager.__init__(self, db, doc_id)`, and cover it with a test that uses a distinctive non-zero `doc_id` (e.g. `doc_id=7`) so any accidental argument swap fails the test loudly.
- Existing tests that mock `handle_existing_document` could mask a regression in the real code path → Mitigation: The new/extended test exercises the real, non-mocked chain end-to-end against an in-memory/temp SQLite DB.
- Downstream code that has silently come to depend on the skip path being a no-op could see new UPDATE side effects once the fix lands → Mitigation: No such dependency was found; treat as a low-likelihood residual risk to watch for in the Phase 3 full-suite run.

## Out of scope

- Changes to `scripts/rag/ingestion/etag_manager.py`.
- Changes to `_handle_existing_file` / the `file://` path.
- Changes to `ingester.py:374`'s call to `handle_existing_document`.
- Documentation updates.
- Refactoring `ETagManager`'s constructor signature.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260727-134054_require.md
- Source plan: plans/20260727-145825_plan.md
- Generated at: 20260728-174511
- Related target files: scripts/rag/ingestion/document_manager.py, scripts/rag/ingestion/etag_manager.py, tests/test_ingester_etag_guard.py
