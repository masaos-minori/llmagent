# Confirm whether browser_fetch capabilities=("web_fetch",) is production code or test-fixture-only (docs/04_mcp_08)

## Priority
Medium

## Summary
`docs/04_mcp_08_tool_capability_naming_convention.md` documents `browser_fetch` as having `capabilities=("web_fetch",)`, but a search of production code did not find this, raising suspicion it may only exist in a test fixture rather than actual production code.

## Reason for Change
If this documented capability value is test-only, an implementer building a tool-capability-aware integration based on this document would use a value that doesn't actually appear in production, causing silent integration failures.

## Implementation Intent
Search both production and test code paths explicitly to determine where `capabilities=("web_fetch",)` actually appears, and correct the documentation to state the real production value (or confirm the test-only value is also used in production, if so).

## Target Files or Areas
`docs/04_mcp_08_tool_capability_naming_convention.md`

## Required Changes
- Search production code (`scripts/mcp_servers/web_search/` or equivalent) for the actual `capabilities` value used by `browser_fetch` in non-test code paths.
- Search test fixtures separately to confirm whether `capabilities=("web_fetch",)` is test-only.
- Update the documentation with the confirmed production value; if the current documented value is test-only, note that explicitly (or remove it and document the real value).

## Acceptance Criteria
The document states the actual production `capabilities` value for `browser_fetch`, with test-only values (if any) clearly distinguished from production ones.

## Testing Expectations
Not required (documentation-only). Verify via `grep -rn "capabilities" scripts/mcp_servers/web_search/ tests/` distinguishing production from test paths before finalizing.

## Documentation Impact
`docs/04_mcp_08_tool_capability_naming_convention.md` corrected with the verified production value.

## Out of Scope
Do not change the actual `capabilities` value in production or test code in this issue — documentation only.

## AI Implementation Instruction
Explicitly distinguish production code paths from test fixture paths in the search — this review's own uncertainty stems from not having made that distinction cleanly, so verify carefully.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §6B (browser_fetchのcapabilities=("web_fetch",)採用)
- Generated at: 2026-08-02
