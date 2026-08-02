# Clarify docs/01_overview-files-04-shared-part2.md events.py "no delivery mechanism" note

## Priority
Medium

## Summary
`docs/01_overview-files-04-shared-part2.md` notes that `events.py` has "(no delivery mechanism)" but does not state which component actually performs event delivery, leaving readers to guess.

## Reason for Change
This is a genuinely easy-to-misunderstand constraint (that `events.py` provides type definitions only, without delivery responsibility) — omitting the actual delivery owner leaves the constraint only half-explained.

## Implementation Intent
Add one sentence naming the component responsible for actual event delivery (the eventbus broker).

## Target Files or Areas
`docs/01_overview-files-04-shared-part2.md`

## Required Changes
- Add a sentence such as: "`events.py` provides only event type definitions; actual delivery is handled by `scripts/eventbus/broker.py`." — confirm the exact responsible module via source inspection before finalizing wording.

## Acceptance Criteria
The `events.py` note explicitly names the module responsible for actual event delivery.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/01_overview-files-04-shared-part2.md` gains one clarifying sentence.

## Out of Scope
Do not describe the full eventbus architecture here — a single pointer sentence is sufficient; broader eventbus documentation is out of scope for this file. Per project policy (AGENTS.md Global Rule 8), do not implement any eventbus-related code changes as part of this documentation issue.

## AI Implementation Instruction
Confirm the actual delivery-responsible module via source inspection (read-only) before writing the sentence — do not assume `scripts/eventbus/broker.py` without verifying.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §4 強化候補 (events.py)
- Generated at: 2026-08-02
