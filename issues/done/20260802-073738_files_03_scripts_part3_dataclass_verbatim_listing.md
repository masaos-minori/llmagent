# Remove verbatim dataclass field enumeration in docs/01_overview-files-03-scripts-part3.md

## Priority
Medium

## Summary
`docs/01_overview-files-03-scripts-part3.md` (~lines 52-58) lists every field of dataclasses like `ServiceWarning` and `ToolApprovalEvent` verbatim in the document body.

## Reason for Change
This is a mechanical transcription of code that goes stale every time a field is added or removed, and is explicitly the kind of "code-derived detail" the documentation policy says to avoid.

## Implementation Intent
Delete the verbatim field enumeration; replace with a one-sentence summary of the responsibility boundary these dataclasses represent, and move the exhaustive field-level detail to a Reference API doc or the source docstrings.

## Target Files or Areas
`docs/01_overview-files-03-scripts-part3.md`

## Required Changes
- Remove the verbatim dataclass field listing (~lines 52-58).
- Replace with a one-sentence summary, e.g. "Audit-event data models (approval events, tool-execution events) are consolidated in `agent/shared/models.py`."
- If no Reference API doc exists yet for this module, note that full field detail should be read from the dataclass definitions/docstrings directly rather than duplicated here.

## Acceptance Criteria
The file no longer enumerates dataclass fields verbatim; the responsibility-boundary summary remains.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/01_overview-files-03-scripts-part3.md` shortened; no information lost (source remains authoritative for field-level detail).

## Out of Scope
Do not create a new Reference API document in this issue unless one already exists to receive this content — if none exists, simply point to the source file/docstrings.

## AI Implementation Instruction
Verify the current dataclass definitions before writing the summary sentence, so the responsibility description matches current code, not the (possibly stale) field list being removed.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §1 (コード説明に寄りすぎている領域), §2 削除候補 item 4
- Generated at: 2026-08-02
