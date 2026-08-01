# Confirm whether docs/00_governance_06 metadata fields (scope, audience, priority, etc.) are actually parsed by any tooling

## Priority
Medium

## Summary
`docs/00_governance_06_ai-reading-metadata.md` documents Existing/Recommended Metadata Fields (scope, audience, priority, etc.), but its own Non-Goals section explicitly states that how AI agents parse/use these fields is out of scope for the document — leaving it unclear whether any code actually consumes them.

## Reason for Change
If no tooling reads these fields, documentation authors may be spending effort maintaining metadata with no operational effect; if tooling does read them, that usage should be documented so authors understand the stakes of getting the fields right.

## Implementation Intent
Search the codebase for any script or tool that parses these frontmatter fields; document the actual usage reality (used by X / not currently used by any known tool) directly in this section.

## Target Files or Areas
`docs/00_governance_06_ai-reading-metadata.md`

## Required Changes
- Grep the repository (`scripts/`, `tools/`) for code that reads frontmatter fields like `scope:`, `audience:`, `priority:`.
- Add a short statement to the Metadata Fields section reporting the finding (used by `<tool/script path>`, or "not currently consumed by any known tooling — informational for human readers only").

## Acceptance Criteria
The document states, based on actual code search, whether these fields are consumed by tooling.

## Testing Expectations
Not required (documentation-only); the underlying investigation is a code search, not a test run.

## Documentation Impact
`docs/00_governance_06` gains a factual usage-reality statement.

## Out of Scope
Do not implement new tooling to consume these fields in this issue, only document current reality.

## AI Implementation Instruction
Base the added statement strictly on actual grep/code-search results; do not assume usage or non-usage without checking.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_governance.md §6 Needs confirmation item (メタデータフィールドの実効性)
- Generated at: 2026-08-02
