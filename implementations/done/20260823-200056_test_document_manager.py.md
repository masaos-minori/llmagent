## Goal
Verify and document that `tests/mcp_servers/rag_pipeline/test_document_manager.py`
requires no code change for this plan, and record a correction to the plan's
Affected areas table entry for this file, which describes methods
(`handle_existing_document()`/`_update_etag()`) that do not exist on the
`DocumentManager` class this file actually imports and tests.

## Scope
- In scope: verification only — no edit to
  `tests/mcp_servers/rag_pipeline/test_document_manager.py` is required by
  this plan.
- Out of scope: `scripts/mcp_servers/rag_pipeline/document_manager.py`
  (unaffected production module — see Assumptions); `scripts/rag/ingestion/document_manager.py`
  and its own test coverage (separate implementation documents; see Details).

## Assumptions
- Confirmed by reading both files: this test file imports
  `from mcp_servers.rag_pipeline.document_manager import DocumentManager`,
  i.e. `scripts/mcp_servers/rag_pipeline/document_manager.py`. That class
  exposes only `_make_helper()`, `list_documents()`, and `delete_document()`
  — no `handle_existing_document()` or `_update_etag()` method exists on it.
- The plan's Affected areas table row for this file ("Update
  `handle_existing_document()`/`_update_etag()` call sites to supply
  mandatory `fetched_at`") describes methods that live on a *different*
  class of the same name, `scripts/rag/ingestion/document_manager.py::DocumentManager`,
  which this test file neither imports nor exercises. Independently
  confirmed via `rg -rn "handle_existing_document|_update_etag" tests/mcp_servers/rag_pipeline/test_document_manager.py`
  — zero matches.
- The plan's "12 existing `fetched_at` references" count for this file is
  accurate (independently re-counted: 12 matching lines), but every one is
  either (a) the ad-hoc `_SCHEMA_SQL` DDL / `_insert_document()` helper's
  raw-SQL fixture plumbing for the `documents` table, or (b) a literal test
  value (e.g. `"2026-01-01T00:00:00Z"`) exercising `list_documents()`'s
  `ORDER BY d.fetched_at DESC` / field-passthrough behavior. None is a call
  to `handle_existing_document()` or `_update_etag()`.
- This file's local `_SCHEMA_SQL` fixture already declares
  `fetched_at TEXT NOT NULL` with no `DEFAULT` clause — already matching the
  plan's target shape for `scripts/db/schema_sql.py` (keep `NOT NULL`,
  remove `DEFAULT`). No fixture-schema edit is needed here.
- All `fetched_at` literal values already used in this file's tests are
  already well-formed canonical UTC strings (`YYYY-MM-DDTHH:MM:SSZ`) — no
  fixture value needs reformatting for this plan's UTC-canonicalization
  requirement.
- `scripts/mcp_servers/rag_pipeline/document_manager.py` itself only reads
  `fetched_at` out of already-NOT-NULL rows (`SELECT`/`ORDER BY`) and never
  constructs or defaults a `fetched_at` value, so it is not a production
  target of this plan either (it is absent from the plan's Affected areas
  table of production files).

## Design decisions
- Treat this as a verification-only document rather than force an
  artificial edit into a file with no actual behavior gap to close —
  editing it would add churn without locking in any new coverage.
- Record the plan-vs-code discrepancy explicitly in this document (rather
  than silently leaving the file untouched) so a later reviewer auditing
  "did every file in the plan's Affected areas table get addressed" can see
  why this one was intentionally left unchanged, and where the real
  `handle_existing_document()`/`_update_etag()` coverage actually lives.

## Alternatives considered
- Editing this file to add a `handle_existing_document()`/`_update_etag()`
  call "to comply with the plan's checklist" — rejected: no such call site
  exists in this file, and the `DocumentManager` it imports does not have
  those methods; fabricating a call would test code this file does not
  exercise.
- Silently closing this row with no note — rejected: would look like an
  accidental skip to a future reviewer rather than a verified conclusion.

## Implementation

### Target file
`tests/mcp_servers/rag_pipeline/test_document_manager.py`

### Procedure
- No code edit required in this file for this plan.
- At implementation time, after `scripts/rag/ingestion/document_manager.py`
  and `scripts/rag/ingestion/etag_manager.py`'s Phase 3 changes land (the
  files that actually own `handle_existing_document()`/`_update_etag()`),
  run this file's suite as a regression check only (see Validation plan) —
  it should be unaffected since it imports neither changed module.

### Method
N/A: verification-only document; no test code to write beyond re-running
the existing suite as a regression check.

### Details
- If a future re-read of this file finds a `handle_existing_document()` or
  `_update_etag()` call site was added after this document was written,
  re-verify this "no change needed" conclusion before assuming it still
  holds.
- The plan's stated Phase 5 intent for this row ("Update
  `handle_existing_document()`/`_update_etag()` call sites to supply
  mandatory `fetched_at`") is actually satisfied by test coverage on
  `scripts/rag/ingestion/document_manager.py`, which (via
  `rg -rln "handle_existing_document" tests/`) lives in
  `tests/rag/ingestion/test_ingestion_freshness.py` and
  `tests/rag/ingestion/test_rag_ingester.py` — neither of which is this
  file. `test_rag_ingester.py` is separately listed in this plan's own
  Phase 5/Traceability list with its own implementation document;
  `test_ingestion_freshness.py` is not listed in this plan's Affected areas
  at all (it already has an implementation document from the sibling plan
  `plans/20260820-094150_plan.md`). Both are outside this document's scope.

## Compatibility considerations
N/A: no code change is made.

## Security considerations
N/A: test-only file, no external input surface, no change made.

## Rollback considerations
N/A: no change is made, so there is nothing to roll back.

## Validation plan
- `uv run pytest tests/mcp_servers/rag_pipeline/test_document_manager.py -v`
  after this plan's other phases land — expect all existing tests to keep
  passing unchanged, confirming this file was correctly outside this plan's
  real edit surface despite its Affected areas table row.
- `rg -rn "handle_existing_document|_update_etag" tests/mcp_servers/rag_pipeline/test_document_manager.py`
  — expect zero matches, confirming the premise of this document holds at
  implementation time too, not just at planning time.

## Out of scope
- `scripts/mcp_servers/rag_pipeline/document_manager.py` production code
  (unaffected by this plan).
- `scripts/rag/ingestion/document_manager.py` and its own test coverage
  (`tests/rag/ingestion/test_ingestion_freshness.py`,
  `tests/rag/ingestion/test_rag_ingester.py`) — separate implementation
  documents.

## Execution Status

##### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| — | — | Pending | — | — | |

##### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

##### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A: not applicable in this phase
- Source requirement: N/A: not applicable in this phase
- Source plan: plans/20260820-095054_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-200056
- Related target files: tests/mcp_servers/rag_pipeline/test_document_manager.py
