# Summarize tool-loop-guard supplement detail in docs/01_overview-arch-02-pipelines.md

## Priority
Low

## Summary
`docs/01_overview-arch-02-pipelines.md` (~lines 45-50) lists 4 tool-loop-guard anomaly types in detail, a level of detail that diverges from the section's stated topic (overall pipeline architecture).

## Reason for Change
The detailed enumeration is more appropriately owned by the tool-loop-guard implementation itself; keeping it here duplicates maintenance effort and distracts from the pipeline-overview narrative.

## Implementation Intent
Compress the 4 anomaly types into a single summary sentence and link to `agent/tool_loop_guard.py` (or the relevant `05_agent_*` detailed doc) for the full specification.

## Target Files or Areas
`docs/01_overview-arch-02-pipelines.md`

## Required Changes
- Replace the 4-item detailed enumeration (~lines 45-50) with a one-line summary, e.g. "The tool loop guard detects abnormal repeated tool-call patterns and forces termination (see `agent/tool_loop_guard.py` for detail)."

## Acceptance Criteria
The section is reduced to a one-line summary with a reference link; no anomaly-type detail remains duplicated in this file.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/01_overview-arch-02-pipelines.md` shortened; detail remains accessible via the linked source/doc.

## Out of Scope
Do not create a new `05_agent_*` detail document in this issue if one does not already cover this — link to the source file directly in that case.

## AI Implementation Instruction
Confirm whether an existing `05_agent_*` document already covers tool-loop-guard detail before deciding the link target; prefer linking to existing documentation over the raw source file if one exists.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §3 要約候補 item 2
- Generated at: 2026-08-02
