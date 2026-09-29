## Goal
Update the `lang` field row in this file's constraints table to remove the
stale `LanguageCode` convention reference and its "Needs confirmation"
parenthetical, describing only the current `_validate_str` non-empty-string
check (REQ-002).

## Scope
- **In-Scope**: The single `lang` field row in this file's constraints table
  (confirmed at line 29).
- **Out-of-Scope**: Any other row in the same table (e.g. the url, content, and
  chunking_strategy rows).
- No code file is modified: `scripts/rag/enums.py` and
  `scripts/rag/ingestion/pipeline_utils.py` are read-only references only.
- Removing the NC-033 entry from the governance inventory (covered by the
  sibling implementation procedure document for
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md`).

## Assumptions
- `LanguageCode` and its sole former user (the now-deleted CrawlTarget class)
  are confirmed absent from current scripts/rag/ source (`rg` zero matches,
  Plan Background) — the fixed wording must not reintroduce any enum
  reference.
- Current `lang` parsing in the ingestion pipeline utilities module uses a
  generic non-empty-string check (already named `_validate_str` in this file's
  own constraints table) with no enum reference, confirmed via Plan Reference
  Files.

## Design decisions
- Scope the fix to the single stale sentence in the `lang` row's cell only, per
  the Issue's own "AI Implementation Instruction" to avoid rewriting the
  surrounding table or document (`skills/python-design` — minimal, targeted
  fix; no restructuring of the table).

## Alternatives considered
- Remove the `lang` row entirely instead of correcting its wording — rejected:
  the row still documents a real, current validation constraint
  (`_validate_str` non-empty-string check); only the stale `LanguageCode`
  clause and the now-moot "Needs confirmation" parenthetical need removal, not
  the row itself.
- Rewrite the entire constraints table for consistency — rejected: out of this
  Plan's scope (Plan Out-of-Scope: only the `lang` row, not a general table
  pass); the adjacent `chunking_strategy` row's own "Needs confirmation"
  parenthetical is a separate, unrelated item not covered by this Plan.

## Implementation
### Target file
`docs/21_rag/rag_05_5-constraints-reference.md`

### Procedure
1. Open `docs/21_rag/rag_05_5-constraints-reference.md` and locate the `lang`
   field row in the constraints table (confirmed at line 29 by direct read
   during this document's generation).
2. Replace that row's description cell with wording that describes only the
   current `_validate_str` non-empty-string check, removing the `LanguageCode`
   convention clause and the "Needs confirmation" parenthetical.

### Method
Direct text replacement (single table-cell content, prose only) — no code,
config, or schema change; no change to the table's row/column structure.

### Details
Current line 29 (confirmed via direct read):
> `lang` validation scope | Any non-empty string accepted at parse time
> (`_validate_str`); the `en`/`ja` value set defined by `LanguageCode`
> (scripts/rag/enums.py) is a convention only, not enforced by either reader
> (Needs confirmation: whether parse-time enforcement is intended)

Replace the description cell with:
> Any non-empty string accepted at parse time (`_validate_str`); no enum or
> closed value set is enforced.

Do not modify the `url`, `content`, or `chunking_strategy` rows, or any other
part of this table or document.

## Compatibility considerations
N/A: documentation-only prose change, no public contract, API, schema, or
runtime behavior affected.

## Security considerations
N/A: no code, credentials, or data-handling change.

## Rollback considerations
Single-cell prose revert via `git revert`/`git checkout` of this file if
needed; no data migration or schema state to unwind.

## Validation plan
Run the applicable documentation checker(s) per `routing.md` Tools → "When to run
which tool":
- `uv run python tools/check_docs_quality.py` (docs file edited)
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_05_5-constraints-reference.md` (docs file edited)
- `uv run python tools/check_docs_content_policy.py` (docs file edited)
- `uv run python tools/check_needs_confirmation_inventory.py` (a Needs
  Confirmation parenthetical is removed by this change)

Expected outcome: all pass; the `lang` row no longer references `LanguageCode`
or an open "Needs confirmation" question.

## Completion criteria
- The `lang` row no longer mentions `LanguageCode` or contains a "Needs
  confirmation" parenthetical.
- The row accurately describes the current `_validate_str` non-empty-string
  check only.
- All checkers listed in Validation plan pass.

## Out of scope
- Removing the NC-033 entry from
  `docs/00_governance/governance_03_issue-and-uncertainty-management.md` —
  handled by the sibling implementation procedure document for that file (seq
  01 of this Plan).
- Any other row in this file's constraints table (e.g. `chunking_strategy`'s
  own separate "Needs confirmation" parenthetical).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `lang` row's description per Implementation > Procedure/Method/Details | Completed | 20260929-151939 | 20260929-151939 | lang row description replaced; stale_detector clean after rewording false-positive backtick scoping (nearby .py path references misattributing _validate_str/LanguageCode/chunking_strategy/CrawlTarget checks) |
| 2 | Run the applicable documentation checker(s) per Validation plan | Completed | 20260929-151939 | 20260929-151939 | Doc checkers run — structure passes; NC-inventory confirms lang-row marker removed (adjacent chunking_strategy marker at line 30 unaffected, out of scope); pre-existing unrelated Related-Documents similarity warnings recorded |

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260927-211410_nc033_remove-obsolete-lang-field-enforcement-question.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-163034_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260929-151401
- **Related target files**: docs/21_rag/rag_05_5-constraints-reference.md