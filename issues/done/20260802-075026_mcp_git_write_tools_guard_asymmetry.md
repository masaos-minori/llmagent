# Confirm git-mcp's lack of additional write-tool guards vs. github-mcp (docs/04_mcp_04_05_git)

## Priority
Medium

## Summary
git-mcp's write tools lack the additional guards (e.g. protected-branch checks) that github-mcp has, and it is unconfirmed whether this asymmetry is an intentional design choice (local git operations are considered the user's own responsibility) or simply unimplemented.

## Reason for Change
If this asymmetry is unintentional, it represents a real safety gap that should be prioritized for implementation; if intentional, leaving it undocumented risks the gap being repeatedly "rediscovered" and misjudged as an oversight needing urgent fixing.

## Implementation Intent
Confirm the design intent with the responsible author/team, and document whichever is true explicitly, rather than leaving the asymmetry unexplained.

## Target Files or Areas
`docs/04_mcp_04_05_git` (or equivalent git-mcp documentation file)

## Required Changes
- Confirm with the document/design owner whether git-mcp intentionally omits github-mcp-style write guards (e.g. under the premise that local git operations are the user's own risk to manage), or whether this is an unimplemented safety feature.
- Document the confirmed answer explicitly, including the risk-acceptance rationale if intentional.

## Acceptance Criteria
The document states, as a confirmed design decision (not silent absence), why git-mcp's write-tool guard posture differs from github-mcp's.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
git-mcp's documentation gains an explicit design-intent statement for this asymmetry.

## Out of Scope
Do not implement additional write-tool guards for git-mcp in this issue — documentation only, unless the confirmation reveals this was intended to be implemented and simply wasn't, in which case file a separate implementation issue.

## AI Implementation Instruction
This requires confirmation from a human design owner — if unconfirmable through available context, register it explicitly as an open Needs Confirmation item rather than asserting either interpretation as fact.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §6B (git-mcp書き込みツールに追加ガードがない理由)
- Generated at: 2026-08-02
