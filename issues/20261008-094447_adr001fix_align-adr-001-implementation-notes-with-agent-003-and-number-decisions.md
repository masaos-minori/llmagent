# Align ADR-001 implementation notes with AGENT-003

## Priority
Medium

## Summary
Revise ADR-001 so its Implementation Notes no longer imply that a missing workflow always stops startup, and make Decision item 4 state that no fallback path exists.

## Background
Source: local investigation notes (memo2.md, ADR-001 section; review finding H01; finding G04 does not apply, see Unresolved Questions). The proposal covers the Decision Details and Implementation Notes sections only; other sections stay as they are.

## Problem
- Implementation Notes read as if the preflight check always stops startup, which contradicts AGENT-003 (the Orchestrator continues in a fallback mode when the workflow definition fails to load).
- Decision item 4 says only "no direct execution path that bypasses the workflow" and does not name the fallback path taken when loading fails.

## Reason for Change
- A reader trusting the ADR would believe INV-01 and INV-05 are fully enforced, while the Orchestrator construction path is not.
- Verified: Decision Details are already numbered 1 to 9, so no renumbering is needed.

## Implementation Intent
- Extend Decision item 4 as in memo2.md (explicit no-fallback wording); keep the existing numbering.
- Replace Implementation Notes so that the preflight check is described as the only current enforcement point until AGENT-003 is resolved.

## Target Files or Areas
- `docs/10_adr/ADR-001-workflow-engine-mandatory.md`

## Required Changes
- Extend Decision item 4 only; do not renumber.
- Apply the revised Implementation Notes from memo2.md, referencing AGENT-003.
- Keep the ADR body in English.

## Constraints
- Only facts confirmed from the documents may be added; claims about code behavior must carry the evidence label required by `skills/DESIGN.md`.
- No source-code line numbers, concrete config values, or implementation counts.

## Acceptance Criteria
- Decision item 4 names the load-failure fallback path as prohibited.
- Implementation Notes state that the Orchestrator fallback is tracked as AGENT-003.
- `docs/10_adr/ADR-001-workflow-engine-mandatory.md` passes the doc checkers listed in `routing.md`.

## Testing Expectations
Run the doc checkers listed in `routing.md` for `docs/` changes (quality, structure, content policy, Known Deviation sync). No code change.

## Documentation Impact
Documentation only: ADR-001 Decision Details and Implementation Notes. ADR-001 Decision content changes, so the ADR Change Protocol in governance_01 applies (see Unresolved Questions).

## Out of Scope
- Fixing AGENT-003 itself (see the wfstartup01 issue).
- Editing adr-index (separate issue).

## Dependencies
- Related: `issues/20261007-153934_wfstartup01_stop-agent-startup-when-workflow-loading-fails.md`.
- adr-index changes for ADR-001 are tracked in the adridx01 issue.

## Unresolved Questions
- memo2.md's premise that ADR-001 Decision items are unnumbered is false (already 1 to 9); only item 4 changes.
- Whether extending item 4 (a Decision content change) requires a new Approval Record under the governance_01 ADR Change Protocol (memo2.md says so for ADR-006/007/009/012/013 only).

## AI Implementation Instruction
Edit only the two named sections of the ADR. Use the text in memo2.md verbatim unless a checker requires a change. Run the doc checkers before finishing. Do not touch code.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094447
- **Related target files**: `docs/10_adr/ADR-001-workflow-engine-mandatory.md`
