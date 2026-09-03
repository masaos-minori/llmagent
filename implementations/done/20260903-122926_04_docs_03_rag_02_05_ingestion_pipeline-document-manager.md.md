## Goal
Complete `REQ-002`'s contract statement for this file by noting that
`ETagManager.update()` rejects an empty `fetched_at` with `ValueError` — the
type-annotation half of `REQ-002` (`fetched_at: str`, not `str | None`) is already
accurately documented in this file's existing signature table and needs no edit.

## Scope
- **In scope**: append a one-sentence note to the `handle_existing_document` table
  row stating the `ValueError`-on-empty-`fetched_at` behavior, cross-linking to the
  `ETagManager` documentation (row 2 of this Plan).
- **Out of scope**: the `handle_existing_document` row's documented return type
  (`-> bool`) and behavior description, which adversarial verification during this
  document's creation found to be inaccurate against the current code (see Design
  decisions — Plan Gap) — fixing that is a separate, unrelated concern from `REQ-002`
  and is not corrected here; the `delete_document_chain`, `__init__`,
  `delete_existing_document`, and `check_consistency` rows; the CLI Entrypoint
  section; modifying `scripts/rag/ingestion/document_manager.py`.

## Assumptions
None beyond the Plan's own Assumptions section.

## Design decisions
- Limit this row's edit strictly to `REQ-002`'s ask (the `ValueError`-on-empty
  behavior) rather than also fixing the `handle_existing_document` row's separately
  discovered inaccuracies, because those are unrelated to `fetched_at`'s
  optionality and are large enough (return type, full branch-by-branch behavior) to
  need their own Plan-scoped correction rather than an incidental fix inside this
  row's document.
- **Plan Gap** (reported per `skills/plan-to-implementation-procedure/workflow.md`
  Step 3, not corrected here): the `handle_existing_document` table row states its
  signature returns `-> bool` and describes returning `True`/`False` to mean
  skip/re-insert. Current code (`scripts/rag/ingestion/document_manager.py:48-102`)
  actually returns `tuple[int, bool, bool]` — `(existing_doc_id, skip_flag,
  replace_chunks_flag)` — with five distinct branches (`force=True`; `file://`+stored
  row missing; `file://`+unchanged; `file://`+changed; non-file+stored row missing;
  non-file+unchanged; non-file+changed calling `ETagManager.update()` before
  returning), not the three-branch, `bool`-returning summary currently documented.
  This is unrelated to `fetched_at`'s optionality (`REQ-002`'s subject) and requires
  its own Plan revision to correct comprehensively — flagging here rather than
  silently fixing or silently leaving unflagged.

## Alternatives considered
- Also correct the `handle_existing_document` row's return-type/behavior description
  in the same edit: rejected — out of `REQ-002`'s scope and large enough (full
  branch-by-branch rewrite) to warrant its own Plan Requirement and evidence review,
  not an incidental fix riding on this row's narrower change.

## Implementation
### Target file
`docs/03_rag_02_05_ingestion_pipeline-document-manager.md`

### Procedure
Append a sentence to the `handle_existing_document` table row's Description cell
noting the `ValueError`-on-empty-`fetched_at` behavior with a cross-link.

### Method
Use `Edit`, anchored on the exact existing table row text shown below — this edit
touches only the Description cell's text, not the Signature cell (already accurate).

### Details
Replace:
```
| `handle_existing_document` | `(url: str, existing_doc_id: int, force: bool, etag\|None, last_modified\|None, fetched_at: str, is_file_url: Callable[[str], bool]) -> bool` | Processes an existing document; returns `True` if the caller should skip insertion. If `force=False` $\rightarrow$ updates ETag via ETagManager; if `file://` URL and SHA-256 hasn't changed $\rightarrow$ skips; if `force=True` $\rightarrow$ deletes the document chain and returns `False` to allow re-insertion. |
```
with:
```
| `handle_existing_document` | `(url: str, existing_doc_id: int, force: bool, etag\|None, last_modified\|None, fetched_at: str, is_file_url: Callable[[str], bool]) -> bool` | Processes an existing document; returns `True` if the caller should skip insertion. If `force=False` $\rightarrow$ updates ETag via ETagManager; if `file://` URL and SHA-256 hasn't changed $\rightarrow$ skips; if `force=True` $\rightarrow$ deletes the document chain and returns `False` to allow re-insertion. `fetched_at` is a required, non-optional `str` parameter in both this method and `ETagManager.update()`; an empty `fetched_at` reaching `ETagManager.update()` raises `ValueError` — see [03_rag_02_06_ingestion_pipeline-supporting-components.md](03_rag_02_06_ingestion_pipeline-supporting-components.md). |
```
Note: this edit deliberately leaves the row's existing (inaccurate) return-type and
branch-description text unchanged — see Design decisions' Plan Gap note; do not use
this edit as an opportunity to silently correct it.

Repository evidence: `docs/03_rag_02_05_ingestion_pipeline-document-manager.md:43`
(existing row text, confirmed `fetched_at: str` already accurate); `scripts/rag/ingestion/document_manager.py:48-57`
(actual signature: `-> tuple[int, bool, bool]`, docstring documenting the 3-tuple
return, confirming the Plan Gap above); `scripts/rag/ingestion/etag_manager.py:34-35`
(`if not new_fetched_at: raise ValueError("new_fetched_at must be a non-empty
string")`) — all confirmed by direct read during this document's creation.

## Compatibility considerations
N/A: documentation-only; no code or behavior change. The added link depends on row 2's
"4.8.1" subsection existing — verify it resolves after row 2's edit lands (per this
Plan's Validation plan link/cross-check).

## Security considerations
N/A: documentation-only, no security-relevant behavior described or changed.

## Rollback considerations
Revert via `git checkout` on this file only; no data migration or dependent artifact
regeneration involved.

## Validation plan
Run `uv run python tools/check_docs_quality.py` and `uv run python
tools/check_docs_consistency.py --domain rag` against this file (per Plan Validation
plan).

## Completion criteria
The `handle_existing_document` row states that `fetched_at` is required/non-optional
and that an empty value raises `ValueError` via `ETagManager.update()`, linked to the
`ETagManager` documentation — without altering the row's separately-flagged (Plan Gap)
return-type/behavior text.

## Out of scope
- Correcting the `handle_existing_document` row's return-type (`-> bool`) and
  branch-behavior description (see Design decisions — Plan Gap; requires a future Plan
  revision).
- The other rows in this document's Class/Module tables and the CLI Entrypoint section.
- Any change to `scripts/rag/ingestion/document_manager.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903-175100 | 20260903-175100 | Adversarially re-verified: table row unchanged since Plan creation; `document_manager.py:48-57` confirms the Plan Gap still real (`-> tuple[int, bool, bool]`, not documented `-> bool`); `etag_manager.py:34-35` confirms the `ValueError`-on-empty-`fetched_at` claim exactly. Edit scoped strictly to REQ-002 per Design decisions — return-type inaccuracy deliberately left untouched |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903-175100 | 20260903-175100 | `check_docs_quality.py`: 0 errors. `check_docs_structure.py`: all checks passed. `check_docs_consistency.py --domain rag`: no findings for this file |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document IS the documentation update |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| Step 1 | Plan Gap discovered: `handle_existing_document` row's documented return type (`-> bool`) and behavior description do not match current code (`-> tuple[int, bool, bool]`, 7 branches) — out of this row's `REQ-002` scope; needs a future Plan revision | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260902-143329_ragfreshness_unify_fetched_at_etag_freshness_docs_remove_null_fill.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-122926
- **Related target files**: docs/03_rag_02_05_ingestion_pipeline-document-manager.md
