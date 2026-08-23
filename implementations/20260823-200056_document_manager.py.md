## Goal

In `scripts/rag/ingestion/document_manager.py`: widen `fetched_at`
(`handle_existing_document()`) and `new_fetched_at` (`_update_etag()`) from
`str | None` to mandatory `str`, so the already-mandatory value read upstream in
`ingester.py` propagates through this file unchanged, with no null-tolerant default
left at either signature.

## Scope

- In scope: `scripts/rag/ingestion/document_manager.py` only — the two named
  signatures and their call sites within this file.
- Out of scope: `ingester.py` (the caller of `handle_existing_document()` — see the
  sibling procedure document for that file), `etag_manager.py`'s `ETagManager.update()`
  (the callee of `_update_etag()` — a separate target file in the source plan, not
  covered by this document).

## Assumptions

- Verified by reading the current source: `handle_existing_document()`'s parameter
  list is `(self, url, existing_doc_id, force, etag: str | None, last_modified: str | None,
  fetched_at: str | None, is_file_url)` — none of these parameters carry a `=` default;
  `fetched_at` is already positionally mandatory, only its type allows `None`. Widening
  its annotation to `str` is a pure type change with no parameter-reordering concern
  (unlike `ingester.py`'s `_get_or_create_document()` — see that file's sibling
  procedure document).
- Verified by reading the current source: `_update_etag()`'s parameter list is
  `(self, doc_id, etag: str | None, last_modified: str | None,
  new_fetched_at: str | None = None)` — `new_fetched_at` is the sole defaulted
  parameter, and it is already last in the list. Dropping its `= None` default to make
  it `new_fetched_at: str` raises no ordering conflict, since no parameter after it
  would need to have a default too.
- Verified by reading the current source: `_update_etag()`'s only call site in this
  file is inside `handle_existing_document()`
  (`self._update_etag(existing_doc_id, etag, last_modified, fetched_at)`), already
  passing `fetched_at` positionally in the fourth slot — no call-site restructuring is
  needed beyond the type now being guaranteed non-`None` by the caller.
- This file has exactly one external caller of `handle_existing_document()`:
  `ingester.py`'s `_get_or_create_document()` (per the plan's Affected-areas Blast
  Radius note) — once that file's own widening lands (see its sibling procedure
  document), the value arriving here is already a plain `str`.

## Design decisions

- Widen both signatures without adding any new runtime validation (`assert`,
  format-checking, etc.) inside this file — per the plan's Design section, this file
  is a pure propagation layer between `ingester.py` and `etag_manager.py`; the
  freshness/format validation itself (fail-closed `_is_stale_update()`) belongs to
  `etag_manager.py`, a separate target file, not to this one.
- Keep `_update_etag()`'s call into `ETagManager(self._db, doc_id).update(...)`
  unchanged in shape (same three positional arguments after `self`) — only the type
  of the third argument changes at this file's boundary; `ETagManager.update()`'s own
  signature widening is a separate document's responsibility.

## Alternatives considered

- Collapsing `handle_existing_document()`'s `fetched_at` and `_update_etag()`'s
  `new_fetched_at` into a single differently-named parameter across both functions —
  rejected: the existing name difference already reflects a real distinction (the
  value being checked-in vs. the value being written on update), and renaming is
  unrelated to this plan's actual requirement (nullability), so it would be
  out-of-scope churn on a high-recent-churn file (3 of 10 commits in the last 30
  days per the plan's Affected-areas table).

## Implementation

### Target file

`scripts/rag/ingestion/document_manager.py`

### Procedure

1. In `handle_existing_document()`: change the `fetched_at: str | None` parameter
   annotation to `fetched_at: str`.
2. In `_update_etag()`: change the `new_fetched_at: str | None = None` parameter to
   `new_fetched_at: str` (drop the default).
3. Confirm (no code change expected) that `handle_existing_document()`'s existing call
   `self._update_etag(existing_doc_id, etag, last_modified, fetched_at)` still type-checks
   cleanly under the new signatures — it already passes `fetched_at` positionally, so no
   edit should be needed here; treat any mypy failure at this line as a signal that an
   upstream caller still supplies `None`.
4. Run `rg -n "fetched_at" scripts/rag/ingestion/document_manager.py` after editing and
   confirm no remaining `str | None` annotation on either parameter.

### Method

Signature widening only — no branch deletion, no new logic, no new abstractions in
this file (contrast with `ingester.py`'s sibling procedure, which also deletes a
fallback branch).

### Details

- No other method in this file touches `fetched_at`/`new_fetched_at`
  (`_handle_existing_file()`, `_is_file_unchanged()`, `delete_existing_document()`,
  `check_consistency()`, and the module-level `delete_document_chain()` do not
  reference either name) — the change is confined to the two named function
  signatures and does not ripple through the rest of the file.
- `handle_existing_document()`'s docstring already documents its three possible return
  tuples in terms of `skip_flag`/`replace_chunks_flag`; no docstring change is implied
  by this type-only widening.

## Compatibility considerations

- The only in-repo caller of `handle_existing_document()` is `ingester.py`'s
  `_get_or_create_document()` — that file's own widening (its sibling procedure
  document) must land together with (or before) this change, or `mypy` will flag a
  type mismatch at the call site; at runtime, Python itself would still accept a
  stray `None` silently since annotations are not enforced, so the two files' changes
  should be treated as one coordinated unit even if committed separately.
- `tests/mcp_servers/rag_pipeline/test_document_manager.py` (separate scope, listed in
  the plan's Affected areas) has 12 existing `fetched_at`-related references that call
  `handle_existing_document()`/`_update_etag()` directly — those call sites must supply
  a concrete `fetched_at` string once `None` is no longer accepted; this document
  does not cover the test file itself.

## Security considerations

N/A: no new external input surface is introduced — `fetched_at`/`new_fetched_at` are
internal values already propagated from a trusted upstream boundary (the crawler/
pipeline_utils read boundary, out of scope here); this change only removes a
null-tolerant default, it does not add new parsing of untrusted input.

## Rollback considerations

- This file is called only from `ingester.py`'s `_get_or_create_document()`, so a
  revert of this file's changes must be paired with a revert of the `ingester.py`
  changes (or of the caller's argument) to avoid a `str | None` vs. `str` mismatch
  surfacing only at `mypy` time rather than at runtime — coordinate reverts across
  both files rather than reverting this one in isolation.
- Unlike `ingester.py` (this plan's highest-churn, single-author file with a specific
  independently-revertable-commit mitigation), this file has no comparable special
  rollback risk called out in the plan; a standard single-commit revert of this file's
  two signature edits is sufficient if needed.

## Validation plan

- `uv run pytest tests/mcp_servers/rag_pipeline/test_document_manager.py -v` — calls
  to `handle_existing_document()`/`_update_etag()` without `fetched_at` fail at the
  type-check level (`uv run mypy scripts/rag/ingestion/document_manager.py`);
  propagation of a supplied `fetched_at` value is confirmed at runtime by existing
  assertions once fixtures are updated (test-file changes are out of scope of this
  document).
- `rg -n "fetched_at: str \| None|new_fetched_at: str \| None" scripts/rag/ingestion/document_manager.py`
  → zero matches after this change.

## Out of scope

- `ingester.py`'s `_get_or_create_document()` (the caller) — see
  `implementations/20260823-200056_ingester.py.md`.
- `etag_manager.py`'s `ETagManager.update()`, `_is_stale_update()`,
  `_update_with_freshness()`, `_update_null_fill()` (the callee) — a separate target
  file in the source plan, not covered here.
- `tests/mcp_servers/rag_pipeline/test_document_manager.py` — a separate Affected-areas
  entry in the source plan.

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
- Related target files: scripts/rag/ingestion/document_manager.py
