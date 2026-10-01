# ETagManager `_is_stale_update()` exception type distinction unresolved

## Priority
Low

## Summary
`ETagManager._is_stale_update()` raises the same `ValueError` for both an invalid
incoming timestamp and an invalid stored timestamp, distinguishable only by message
text. Get an owner decision on whether distinct exception types are intended, and
either formalize the decision or implement the split.

## Background
`docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` documents (added
2026-09-03, per `implementations/done/20260903-122926_02_docs_03_rag_02_06...md`):
both `_is_stale_update()` raise sites use the same `ValueError` type — the message
text (`"Invalid incoming timestamp: ..."` vs `"Invalid stored timestamp: ..."`) is
the only current distinguishing mechanism; no separate exception classes exist for
the two cases. That implementation procedure explicitly recorded this as a Needs
Confirmation item rather than resolving it, and no subsequent issue was filed to
carry the question forward — repository-wide search found no issue, plan, or
implementation procedure targeting this specific question.

## Problem
Any caller that needs to distinguish "the crawler just fetched a corrupt/malformed
timestamp" from "a previously stored timestamp in the database is corrupt" today has
no reliable way to do so except parsing the exception's message string — a fragile
pattern that breaks silently if the message wording changes.

## Reason for Change
This is a design question that has sat undecided since 2026-09-03, documented only
as an inline Needs Confirmation marker with no owner follow-up. Left unresolved, it
risks being silently treated as permanent design ("this is just how it works") when
no such decision was ever actually made.

## Implementation Intent
Get an owner decision between:
(a) formalize current behavior as intentional — a single `ValueError` type is
    sufficient, no caller currently needs to distinguish the two cases; or
(b) introduce two distinct exception types (e.g. subclasses of `ValueError` to
    preserve existing `except ValueError` call sites) for the incoming-timestamp and
    stored-timestamp cases, and update any caller that would benefit from
    distinguishing them.
Do not invent a rationale for either option — resolve via owner confirmation.

## Target Files or Areas
- `scripts/rag/ingestion/etag_manager.py` (`_is_stale_update()`)
- `docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md` (Needs Confirmation marker to resolve)
- Callers of `ETagManager`/`_is_stale_update()`: Unknown — requires a caller search if option (b) is chosen

## Required Changes
- Obtain owner decision between options (a)/(b) above.
- If (a): remove the Needs Confirmation marker in `rag_02_06...md` and replace with
  a plain statement that this is accepted current behavior.
- If (b): add the new exception types, update `_is_stale_update()`'s raise sites,
  check every caller for compatibility, and update the documentation accordingly.

## Constraints
Any new exception type must remain a `ValueError` subclass (or the change must
audit and update every existing `except ValueError` call site) to avoid silently
breaking current error handling.

## Acceptance Criteria
- An explicit owner decision is recorded (accept current behavior, or implement
  distinct exception types).
- `rag_02_06_ingestion_pipeline-supporting-components.md`'s Needs Confirmation
  marker for this item is resolved (removed or replaced with a plain statement of
  accepted behavior).
- If option (b) is chosen: distinct exception types exist, all existing callers
  still function correctly, and a unit test covers both raise sites individually.

## Testing Expectations
If option (b) is chosen: unit tests asserting each raise site produces its own
exception type. If option (a): not required — documentation-only.

## Documentation Impact
Yes. `rag_02_06_ingestion_pipeline-supporting-components.md`'s Needs Confirmation
marker must be resolved either way (removed if closed as "no change intended", or
replaced with new-behavior documentation if option (b) is implemented).

## Out of Scope
- Any other exception-handling pattern in `scripts/rag/ingestion/` not related to
  `_is_stale_update()`'s two raise sites.

## Dependencies
N/A: none.

## Unresolved Questions
Whether any current or planned caller actually needs to distinguish
invalid-incoming-timestamp from invalid-stored-timestamp — this determines whether
option (a) or (b) above is correct, and needs owner input rather than being guessed.

## AI Implementation Instruction
Do not implement option (b) speculatively without an explicit owner decision — this
issue's primary deliverable is surfacing the question, not picking an answer. If
option (b) is confirmed, search for every call site before changing the exception
type, and keep new types as `ValueError` subclasses unless every call site is
updated in the same change.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260930-135010
- **Related target files**: scripts/rag/ingestion/etag_manager.py, docs/21_rag/rag_02_06_ingestion_pipeline-supporting-components.md
