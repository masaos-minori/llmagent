# Implementation Procedure: tests/rag/ingestion/test_rag_ingestion_pipeline.py

## Goal

Update the stale docstring comment in `_make_fake_sqlite_helper()` that names the
about-to-be-deleted `_handle_existing_file` even though the fixture it documents
actually exercises `handle_existing_document()`'s SQL access pattern.

## Scope

**In-Scope**
- The docstring comment line inside `_make_fake_sqlite_helper()`: "This is needed
  because `_handle_existing_file` accesses `stored["etag"]`, `stored["last_modified"]`."

**Out-of-Scope**
- Any other part of this file — the fixture's actual behavior (row-factory setup,
  mocked `execute`/`fetchall`) is correct and unaffected; only the comment's method-name
  reference is stale.
- The fixture's functional behavior — unchanged; `handle_existing_document()` accesses
  `stored["etag"]`/`stored["last_modified"]` via the identical SQL query pattern the
  comment already describes, so only the named method needs correcting, not the
  explanation itself.

## Assumptions

- The comment is genuinely stale and not a currently-accurate reference — confirmed by
  reading `document_manager.py`: `_handle_existing_file()` (being deleted by the
  companion procedure) and `handle_existing_document()` (surviving) both run the same
  `SELECT etag, last_modified FROM documents WHERE doc_id = ?` query and both access
  `stored["etag"]`/`stored["last_modified"]` from the row-factory result — so the
  fixture's row-factory requirement is real and applies equally to whichever method is
  in use; only the named method in the comment needs to change to the surviving one.
- No other file in the repository has an equivalent stale reference to
  `_handle_existing_file` — confirmed via `rg -n "_handle_existing_file" scripts/
  tests/` (excluding `mutants/`), which returns only this file's comment and the
  method's own definition in `document_manager.py`.

## Design decisions

- Minimal, comment-only edit: replace `_handle_existing_file` with
  `handle_existing_document` in the docstring sentence; no rewording of the surrounding
  explanation, since the underlying reason (row-factory needed for dict-like column
  access) remains accurate for the surviving method.

## Alternatives considered

- Rewrite the whole docstring to describe `handle_existing_document()`'s broader
  three-branch behavior (force / file-unchanged / file-changed) instead of a one-line
  method-name swap — rejected: this fixture's docstring only needs to explain why
  `row_factory` is set, which is a data-access-shape concern independent of which
  specific method reads the row; a broader rewrite would be unrequested scope creep for
  a comment-only fix.

## Implementation

### Target file
`tests/rag/ingestion/test_rag_ingestion_pipeline.py`

### Procedure
1. Locate the docstring inside `_make_fake_sqlite_helper()`.
2. Replace `_handle_existing_file` with `handle_existing_document` in the sentence
   explaining why `row_factory` is needed.
3. Re-run `rg -n "_handle_existing_file" scripts/ tests/` (excluding `mutants/`) after
   the edit to confirm this was the last remaining reference outside
   `document_manager.py`'s own (now-deleted) definition.

### Method
Direct string edit inside a docstring — no code logic change.

### Details
- No test behavior changes — this is purely a comment correction; the fixture's
  `MagicMock`/`row_factory` setup is untouched.

## Compatibility considerations

N/A: comment-only change, no runtime behavior affected.

## Security considerations

N/A: comment-only change.

## Rollback considerations

- Trivially revertable: a comment-only change with no dependency on any other file's
  state (unlike the companion `document_manager.py` deletion and
  `test_ingestion_freshness.py` new test, this edit has no ordering constraint relative
  to those — it can land independently at any point).

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/rag/ingestion/test_rag_ingestion_pipeline.py | Regression (no behavior change expected) | `uv run pytest tests/rag/ingestion/test_rag_ingestion_pipeline.py -v` | All existing tests continue to pass unchanged |
| Repo-wide | Zero stale-reference re-check | `rg -n "_handle_existing_file" scripts/ tests/` (excluding `mutants/`) | Zero matches after `document_manager.py`'s deletion also lands |

## Out of scope

- Any functional test addition to this file — not requested by the source plan for this
  target.

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
- Source plan: plans/20260820-100528_plan.md
- Source implementation procedure: N/A: not applicable in this phase
- Generated at: 20260823-202324
- Related target files: tests/rag/ingestion/test_rag_ingestion_pipeline.py
