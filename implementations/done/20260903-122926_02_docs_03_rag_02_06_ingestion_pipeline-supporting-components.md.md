## Goal
Extend `ETagManager`'s description with the invalid-incoming-timestamp,
invalid-stored-timestamp, equal-timestamp, and missing-stored-timestamp outcomes
(`REQ-004` through `REQ-007`), and confirm Null Fill Mode's absence as the current
implementation's only update mode (`REQ-003`) — this document is already correct on
the freshness-guard and both-absent-early-return behavior and needs no change to that
existing content.

## Scope
- **In scope**: add a new "4.8.1" subsection under the existing "## 4.8 ETagManager"
  section covering: Null Fill Mode absence confirmation, the accepted timestamp
  format (ISO 8601 + UTC normalization), invalid-incoming/invalid-stored-timestamp
  `ValueError` outcomes, the equal-timestamp outcome, and the missing/empty
  stored-`fetched_at` outcome.
- **Out of scope**: the existing "4.8 ETagManager" intro paragraph, Public Methods
  table, and Boundary Conditions bullet (already accurate — no Requirement in this
  Plan targets them for change); the "4.9 Configuration" section; documenting the
  missing-`new_fetched_at`-raises-`ValueError` check (not required by any Requirement
  targeting this file — `REQ-002` targets the ingester/document-manager documents
  instead); modifying `scripts/rag/ingestion/etag_manager.py`.

## Assumptions
None beyond the Plan's own Assumptions section.

## Design decisions
- Add a new "4.8.1" subsection rather than editing the existing intro paragraph or
  Public Methods table — this keeps the already-accurate existing content untouched
  (respecting this row's narrower Requirement scope) while giving the new edge-case
  detail its own addressable heading that rows 3 and 4 (the ingester and
  document-manager documents) can cross-link to.
- Present `Invalid incoming timestamp`/`Invalid stored timestamp` as message-text-only
  distinctions, per the Plan's own Assumptions section and `REQ-006`'s phrasing — do
  not imply a stable, code-enforced exception-type contract that does not exist
  (`UNK-01`).

## Alternatives considered
- Fold the edge cases into the existing intro paragraph instead of a new subsection:
  rejected — the paragraph is already accurate and concise; appending five distinct
  edge-case behaviors to it would make it unwieldy and harder for rows 3/4 to link to a
  specific location.

## Implementation
### Target file
`docs/03_rag_02_06_ingestion_pipeline-supporting-components.md`

### Procedure
Insert a new "### 4.8.1 Freshness Comparison: Edge Cases and Error Handling"
subsection immediately after the existing "Boundary Conditions" bullet and before
"## 4.9 Configuration".

### Method
Use `Edit`, anchoring on the exact existing "## 4.9 Configuration" heading line to
insert immediately before it.

### Details
Insert the following content immediately before the `## 4.9 Configuration` heading:
```markdown
### 4.8.1 Freshness Comparison: Edge Cases and Error Handling

- **Only current update mode:** Freshness Mode (above) is `ETagManager`'s only update
  mode — Null Fill Mode / `COALESCE`-based missing-`fetched_at` handling has been
  fully removed; no `_update_null_fill`, `null_fill`, or `COALESCE` reference remains
  anywhere under `scripts/rag/ingestion/`.
- **Timestamp format:** both the incoming and stored `fetched_at` are parsed via
  `datetime.fromisoformat()` after replacing a trailing `Z` with `+00:00`; a
  timezone-naive value is accepted and normalized to UTC (`replace(tzinfo=UTC)`).
- **Invalid incoming timestamp:** if the incoming `fetched_at` fails to parse,
  `_is_stale_update()` raises `ValueError(f"Invalid incoming timestamp: {value}")`.
- **Invalid stored timestamp:** if the stored `fetched_at` fails to parse,
  `_is_stale_update()` raises `ValueError(f"Invalid stored timestamp: {value}")`. Both
  cases raise the same `ValueError` type — the message text is the only current
  distinguishing mechanism; no separate exception classes exist for the two cases
  (Needs confirmation: whether distinct exception types are intended in the future).
- **Equal timestamps:** the staleness check is a strict `new_dt < stored_dt` — an
  incoming `fetched_at` equal to the stored value is **not** treated as stale, so the
  update proceeds.
- **Missing/empty stored `fetched_at`:** if no `documents` row exists for the
  `doc_id`, or its stored `fetched_at` is empty/absent (e.g. a pre-migration row),
  `_is_stale_update()` returns `False` (not stale) without attempting to parse it —
  the incoming value always wins in this case.
- **Both `etag` and `last_modified` absent:** as already documented above, `update()`
  returns early without any database write in this case — no staleness check occurs.

See [03_rag_02_04_ingestion_pipeline-ingester.md](03_rag_02_04_ingestion_pipeline-ingester.md)
and [03_rag_02_05_ingestion_pipeline-document-manager.md](03_rag_02_05_ingestion_pipeline-document-manager.md)
for how callers rely on this contract, and
[03_rag_05_4-error-handling-reference.md](03_rag_05_4-error-handling-reference.md) for
the `ValueError` conditions in the shared error-handling reference table.
```
Repository evidence: `scripts/rag/ingestion/etag_manager.py:49-78` (`_is_stale_update()`
full body: timestamp parsing, both raise sites, missing-stored-timestamp early
`return False`, strict `<` comparison); `:36-37` (both-`None` early return, already
documented in this file's existing text); `grep -rn "_update_null_fill|null_fill|COALESCE"
scripts/rag/ingestion/` returns no matches (confirmed during this document's
creation) — all confirmed by direct read.

## Compatibility considerations
N/A: documentation-only; no code or behavior change. Rows 3 and 4 (ingester and
document-manager documents) link to this new subsection — verify those links resolve
once this row's edit lands (per this Plan's Validation plan manual cross-check).

## Security considerations
N/A: documentation-only, no security-relevant behavior described or changed.

## Rollback considerations
Revert via `git checkout` on this file only; no data migration or dependent artifact
regeneration involved. Reverting this row would break the links added by rows 3 and 4
— coordinate any rollback across those documents.

## Validation plan
Run `uv run python tools/check_docs_quality.py` and `uv run python
tools/check_docs_consistency.py --domain rag` against this file (per Plan Validation
plan); manually confirm rows 3/4 link here rather than duplicating this content (per
Plan Validation plan's manual cross-check row).

## Completion criteria
The new "4.8.1" subsection documents Null Fill Mode's absence, the accepted timestamp
format with UTC normalization, both invalid-timestamp `ValueError` outcomes, the
equal-timestamp outcome, and the missing-stored-timestamp outcome — each traceable to
`_is_stale_update()`'s code.

## Out of scope
- The existing "4.8 ETagManager" intro paragraph, Public Methods table, and Boundary
  Conditions bullet.
- The "4.9 Configuration" section.
- The missing-`new_fetched_at` `ValueError` check (covered by rows 3/4's own scope,
  `REQ-002`, not this row).
- Any change to `scripts/rag/ingestion/etag_manager.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260903-174700 | 20260903-174700 | Adversarially re-verified: `_is_stale_update()`'s full body (lines 36-78) matches every claim exactly — timestamp parsing, both raise sites, missing-stored early return, strict `<` comparison; `grep` confirms zero `_update_null_fill`/`null_fill`/`COALESCE` remnants |
| 2 | Add or update tests per Validation plan | N/A | — | — | No tests required — documentation-only (Plan Tests section) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260903-174700 | 20260903-174700 | `check_docs_quality.py`: 0 errors. `check_docs_structure.py`: all checks passed. `check_docs_consistency.py --domain rag`: 1 warning for `fromisoformat()` — manually confirmed benign false positive (Python stdlib `datetime` method, not a project symbol; checker only scans `scripts/`) |
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
- **Requirement ID**: REQ-003, REQ-004, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/20260902-143329_ragfreshness_unify_fetched_at_etag_freshness_docs_remove_null_fill.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260903-085718_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-122926
- **Related target files**: docs/03_rag_02_06_ingestion_pipeline-supporting-components.md
