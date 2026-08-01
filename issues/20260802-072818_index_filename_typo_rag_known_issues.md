# Fix incorrect filename reference at docs/00_index.md line 128 (`-part1` suffix does not exist)

## Priority
Low

## Summary
Line ~128 of `docs/00_index.md` references `03_rag_90_inconsistencies_and_known_issues-part1.md`, but the actual file (confirmed via `ls`) is `03_rag_90_inconsistencies_and_known_issues.md` — no `-part1` suffix exists. The correct filename is already used elsewhere in the same document (~line 51) and in `docs/00_governance_08` (~line 15).

## Reason for Change
A broken file reference in the RAG known-bugs pointer misleads readers/agents trying to open the referenced file.

## Implementation Intent
Direct text correction; no structural change needed.

## Target Files or Areas
`docs/00_index.md` (~line 128)

## Required Changes
- Change `03_rag_90_inconsistencies_and_known_issues-part1.md` to `03_rag_90_inconsistencies_and_known_issues.md` at ~line 128.

## Acceptance Criteria
All references to this file within `docs/00_index.md` use the correct filename (no `-part1` suffix anywhere).

## Testing Expectations
Not required (documentation-only). Verify with `ls docs/03_rag_90_inconsistencies_and_known_issues.md` and `grep -rn "part1" docs/00_index.md` after the fix.

## Documentation Impact
`docs/00_index.md` corrected; no other files affected.

## Out of Scope
Do not touch other file references in the same document beyond this one confirmed typo.

## AI Implementation Instruction
This is a confirmed factual fix (verified via `ls`), not a Needs Confirmation item — apply directly.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §1 (再構成の基本方針 item 5), §5 例3
- Generated at: 2026-08-02
