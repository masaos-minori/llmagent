# Allow start and end status updates for short documentation procedures

## Priority
Low

## Summary
Let `code-implementation` update the Execution Status of a documentation-only procedure with at most two rows at its start and at its completion instead of at every step transition.

## Background
Evidence (`Explicit in code`): `skills/code-implementation/workflow.md` "Progress recording during Steps 3-6" requires an Execution Status write at every step transition, and `tools/set_execution_status.py` can mark several rows in one call (`--step 1,4`, `--all`). In the 2026-11-27 session a procedure of two rows took five to seven separate calls.

## Problem
Short, documentation-only procedures pay the same per-transition call cost as long code procedures.

## Reason for Change
Tool calls and tokens per procedure; the persisted record exists to recover an interrupted session.

## Implementation Intent
Relax the cadence only where a rerun is cheap and idempotent, and keep per-transition writes everywhere else.

## Target Files or Areas
- `skills/code-implementation/workflow.md`

## Required Changes
- Define the condition (documentation-only, at most two rows, no code or test file changed) and the reduced cadence (one write at the start marking the first row `In Progress`, one at completion marking all rows).
- State that any other procedure keeps the per-transition writes.

## Constraints
- The change reduces the interruption-recovery granularity, so it needs the owner's acceptance.
- `skills/code-implementation/workflow.md` ceiling 42118 B (40181 B on 2026-11-27).

## Acceptance Criteria
- [ ] The condition and the reduced cadence are stated.
- [ ] Procedures outside the condition are unchanged.

## Testing Expectations
`tools/check_skill_size.py`, `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`.

## Documentation Impact
Yes. The Progress recording section.

## Out of Scope
- Changing the Execution Status structure or the Row mapping.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether the owner accepts the lower recovery granularity for these procedures.

## AI Implementation Instruction
Do not decide the policy yourself; write the accepted text only after the owner decides.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120109
- **Related target files**: `skills/code-implementation/workflow.md`
