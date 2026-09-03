## Goal
Add an invalid-`fetched_at` row to the `RagIngester` error table, citing the two
distinct `ValueError` messages (`Invalid incoming timestamp` / `Invalid stored
timestamp`) as the current distinguishing mechanism (`REQ-006`).

## Scope
- **In scope**: add one row to the existing `## RagIngester` table.
- **Out of scope**: the existing `Crawler`, `ChunkSplitter`, `RagPipeline` tables and
  `Implementation Notes`; the `## Pipeline Utils — Artifact Validation` section added
  by the sibling `plans/done/20260903-085152_plan.md`'s row 6 for this same file (a
  separate, non-overlapping insertion point — see Assumptions); modifying
  `scripts/rag/ingestion/etag_manager.py`, `document_persistence.py`, or
  `ingester.py`.

## Assumptions
- **Cross-Plan awareness (non-conflicting)**: `implementations/20260903-121706_06_docs_03_rag_05_4-error-handling-reference.md.md`
  (`plans/done/20260903-085152_plan.md`'s row 6, a separate, already-archived Plan)
  also targets this file, inserting a new `## Pipeline Utils — Artifact Validation`
  section immediately before the existing `## RagIngester` heading. This row's edit
  (a new row inside the existing `## RagIngester` table) does not touch that heading
  or any content before it — no conflict expected regardless of which Plan's edit
  lands first.

## Design decisions
- Traced the actual propagation path (not just the raise site) before writing the
  "Action" column, since the existing table's other rows describe user-visible
  outcome, not just the exception type: `ETagManager.update()`'s `ValueError`
  (`etag_manager.py:59-60,75-76`) is raised inside `_is_stale_update()`, called from
  `DocumentManager._update_etag()` (`document_manager.py:104-112`), called from
  `handle_existing_document()`, called from `DocumentStore.get_or_create()`
  (`document_persistence.py:61-65`), called from `RagIngester.ingest_url_group()`
  (`ingester.py:279`) — a call site with no `ValueError`-specific `except` clause
  around it (only two `except ChunkFormatError` clauses exist in this method, for the
  earlier chunk-reading step, and they don't cover this call). The exception
  therefore propagates up to `RagIngester._process_url_groups()`'s catch-all
  (`ingester.py:379-385`, `except (OSError, RuntimeError, ValueError):
  logger.exception(...); results.append(IngestUrlResult.unexpected_failure(url))`) —
  the identical propagation path already documented for the existing "Invalid `lang`
  value" row, since `DocumentStore.get_or_create()`'s own `validate_lang()` check
  (`document_persistence.py:51-54`) raises its `ValueError` from the same call site.
  Match that row's existing "skip URL group; `ERROR` (with traceback)" phrasing for
  consistency, since the underlying mechanism is identical.

## Alternatives considered
- Cite only the raise site (`etag_manager.py`) without stating the propagation
  outcome: rejected — every other row in this table states the user-visible
  Action, not just where the exception originates; omitting it here would be
  inconsistent with the table's established format.

## Implementation
### Target file
`docs/03_rag_05_4-error-handling-reference.md`

### Procedure
Append one row to the existing `## RagIngester` table.

### Method
Use `Edit`, anchored on the exact existing table's last row shown below.

### Details
Replace:
```
| Invalid `lang` value | Raises `ValueError`; skips the URL group; logs an `ERROR` with traceback |
```
with:
```
| Invalid `lang` value | Raises `ValueError`; skips the URL group; logs an `ERROR` with traceback |
| Invalid `fetched_at` (incoming or stored) | `ETagManager._is_stale_update()` raises `ValueError` — `Invalid incoming timestamp: {value}` or `Invalid stored timestamp: {value}` (message text is the only current distinction; no separate exception classes). Uncaught at the call site (`RagIngester.ingest_url_group()`), it propagates to the same catch-all as "Invalid `lang` value" above: skips the URL group; logs an `ERROR` with traceback. See [03_rag_02_06_ingestion_pipeline-supporting-components.md section 4.8.1](03_rag_02_06_ingestion_pipeline-supporting-components.md#481-freshness-comparison-edge-cases-and-error-handling). |
```
Repository evidence: `scripts/rag/ingestion/etag_manager.py:56-60,71-76` (both raise
sites); `scripts/rag/ingestion/document_manager.py:104-112` (`_update_etag`, the only
caller of `ETagManager.update()`); `scripts/rag/ingestion/document_persistence.py:61-65`
(`get_or_create()` calling `handle_existing_document()`, and `:51-54`
`validate_lang()`'s `ValueError`, confirming the identical propagation path already
documented for "Invalid `lang` value"); `scripts/rag/ingestion/ingester.py:279`
(`get_or_create()` call site inside `ingest_url_group()`, with no `ValueError`-specific
`except` clause around it — only `except ChunkFormatError` at lines 223/241, for a
different, earlier step); `:379-385` (`_process_url_groups()`'s catch-all) — all
confirmed by direct read during this document's creation.

## Compatibility considerations
N/A: documentation-only; no code or behavior change. The added link depends on the
sibling Plan's row 2 equivalent — actually this Plan's own row 2 — "4.8.1" subsection
existing; verify it resolves after that row's edit lands (per this Plan's Validation
plan link/cross-check).

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
The `RagIngester` table contains a row for invalid `fetched_at` citing both
`ValueError` messages and stating the same skip-URL-group/`ERROR`-with-traceback
outcome as the existing "Invalid `lang` value" row, linked to the `ETagManager`
edge-case subsection.

## Out of scope
- The existing `Crawler`, `ChunkSplitter`, `RagPipeline` tables and `Implementation
  Notes` section.
- The `## Pipeline Utils — Artifact Validation` section (sibling Plan's row 6).
- Any change to `scripts/rag/ingestion/etag_manager.py`, `document_persistence.py`,
  `document_manager.py`, or `ingester.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | `check_docs_quality.py`, `check_docs_consistency.py --domain rag` |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — | This document IS the documentation update |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260902-143329_ragfreshness_unify_fetched_at_etag_freshness_docs_remove_null_fill.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-122926
- **Related target files**: docs/03_rag_05_4-error-handling-reference.md
