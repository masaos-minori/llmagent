# Consolidate duplicate ADR-010/ValueError discrepancy into NC-036

## Priority
High

## Summary
Remove the un-ID'd ADR-010 Decision #9 vs `call_rag_service()` ValueError handling paragraph from Part 1 (Known Issues) of `docs/00_governance_03_issue-and-uncertainty-management.md`. The same discrepancy is already tracked as NC-036 in Part 2 (Needs Confirmation Inventory). The floating paragraph lacks an ID, proper template fields, and duplicates NC-036's content.

## Background
During the Known Issues re-verification (part of the RAG parse error fix effort), a paragraph was inserted between EVENTBUS-007 and CI-008 in Part 1 describing the ADR-010 Decision #9 vs `ValueError` handling mismatch. This paragraph begins with "A narrower, genuine discrepancy was found..." and ends with "...file a new, narrowly-scoped Known Issue or Needs Confirmation entry for this specific Decision #9 vs. `ValueError`-handling question if it is to be tracked."

Separately, NC-036 in Part 2 tracks this exact same discrepancy with full template fields (ID, Source File, Section, Question, Evidence, Impact, Required Action, Status, Assigned To, Priority, etc.), assigned to @data-eng with High priority.

## Problem
The same discrepancy appears twice in the document:
1. As an un-ID'd floating paragraph in Part 1 (Known Issues) between EVENTBUS-007 and CI-008 (around line 217)
2. As a properly templated NC-036 entry in Part 2 (Needs Confirmation Inventory)

The floating paragraph in Part 1 violates the Part 1 entry template (which requires 17 fields including ID). It also creates confusion about whether this discrepancy needs separate tracking in both parts. Since NC-036 already captures the full details with proper fields, the Part 1 paragraph is redundant.

## Reason for Change
Duplicate tracking across parts undermines the single-system-of-record principle. Part 1 is for Known Issues (document-code mismatches, design deviations); Part 2 is for Needs Confirmation (unverified claims). The ADR-010/ValueError question is classified as a Needs Confirmation because the intent is undetermined — it belongs in Part 2, not Part 1.

## Implementation Intent
Delete the floating paragraph from Part 1 (the one starting "A narrower, genuine discrepancy was found..." and ending "...if it is to be tracked."). Ensure the transition from EVENTBUS-007 to CI-008 is clean with appropriate spacing. Verify that NC-036 in Part 2 retains all its fields unchanged.

## Target Files or Areas
- `docs/00_governance_03_issue-and-uncertainty-management.md` (Part 1 between EVENTBUS-007 and CI-008)

## Required Changes
- Delete the un-ID'd paragraph between EVENTBUS-007 and CI-008 (approximately lines 217-218)
- Also delete the orphaned `- **Resolution Target**: Next RAG architecture review` line that follows (line 221) — it has no associated entry header
- Verify NC-036 in Part 2 is untouched
- Verify no trailing blank-line artifacts remain

## Constraints
- Do not modify NC-036 in Part 2
- Do not modify any other Known Issue entries
- Do not add a new ID to the deleted paragraph — the decision is removal, not conversion
- Preserve the EventBus-specific verification paragraph (REQ-006) that immediately precedes the deleted block

## Acceptance Criteria
- [ ] The un-ID'd "narrower, genuine discrepancy" paragraph is removed from Part 1
- [ ] The orphaned `- **Resolution Target**: Next RAG architecture review` line is removed
- [ ] NC-036 in Part 2 remains intact with all 15 fields
- [ ] The EventBus-specific verification (REQ-006) paragraph is preserved
- [ ] No other entries are modified
- [ ] No other file modified

## Testing Expectations
Manual review comparing pre-edit and post-edit versions. Run `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md` to verify structural integrity.

## Documentation Impact
Governance document cleanup. Aligns Part 1 with the rule that only properly-ID'd Known Issue entries belong in Active Items.

## Out of Scope
- Resolving NC-036 itself (that is a separate action requiring @data-eng judgment)
- Modifying Part 3 (Canonical Source Conflict) or Part 4 (Configuration Drift)
- Adding automated deduplication checks between Part 1 and Part 2

## Dependencies
- None

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Edit only `docs/00_governance_03_issue-and-uncertainty-management.md`. Delete the paragraph starting with "A narrower, genuine discrepancy was found during this same re-verification" through the end of that block, plus the following orphaned `- **Resolution Target**:` line. Do not modify NC-036 or any other entry. After editing, run `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md` to confirm no structural issues.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-120032
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
