# Measure and reduce the Step 0 load of the pipeline skills

## Priority
Low

## Summary
Measure what each pipeline phase loads at Step 0 and how often each section is used, move rarely used sections to edge files, and lower the baseline ceilings accordingly.

## Background
Evidence (`Explicit in code`): on 2026-11-27 `skills/issue-to-plan/workflow.md` was 42111 B, `skills/code-implementation/workflow.md` 40181 B, `skills/plan-to-implementation-procedure/workflow.md` 34635 B, and `skills/git-commit-and-sync/workflow.md` 22706 B; `tools/check_skill_size_baseline.txt` records per-invocation load totals in its header comments. The edge-file pattern already exists and was applied in the `skillsize` work and again on 2026-11-27. Usage frequency per section is not recorded anywhere (`不明`).

## Problem
The base workflow files remain large, and what to move next is a guess without frequency data.

## Reason for Change
Input tokens on every cycle of every phase; no correctness risk.

## Implementation Intent
Measure first, then move only sections shown to be rarely needed, verbatim.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md`
- `skills/issue-to-plan/workflow-edge.md`
- `skills/code-implementation/workflow.md`
- `skills/code-implementation/workflow-edge.md`
- `skills/plan-to-implementation-procedure/workflow.md`
- `skills/plan-to-implementation-procedure/workflow-edge.md`
- `tools/check_skill_size_baseline.txt`

## Required Changes
- Define the measurement: for each phase, the bytes of the Step 0 file list and a count of how many past cycles (from archived plans and procedures) reached each section's trigger.
- Select sections whose trigger was reached in a small share of cycles, and move them verbatim to the edge file with a pointer in the existing form.
- Lower the baseline ceilings with `tools/check_skill_size.py --update-baseline` only after the move.

## Constraints
- No rule text is dropped or reworded; moves are verbatim and compared.
- Edge files stay under 16384 B.

## Acceptance Criteria
- [ ] The measurement and its result are recorded in the change description.
- [ ] Moved sections are identical to the originals.
- [ ] The skill checks pass and the ceilings are lower.

## Testing Expectations
`tools/check_skill_size.py`, `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`; a whitespace-normalized comparison of each moved section.

## Documentation Impact
Yes. The listed skill files.

## Out of Scope
- Changing any workflow's rules or steps.

## Dependencies
- Optional: issues/20261127-120106_flowopt008_markdown-section-move-tool.md (a verified move tool), and issues/20261127-120059_flowopt001_skill-size-fallout-check.md (headroom reporting).

## Unresolved Questions
- `不明`: how to count section use per cycle from the archived documents.

## AI Implementation Instruction
Measure before moving. Stop and report if a section's trigger frequency cannot be established.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120111
- **Related target files**: `skills/issue-to-plan/workflow.md`, `skills/issue-to-plan/workflow-edge.md`, `skills/code-implementation/workflow.md`, `skills/code-implementation/workflow-edge.md`, `skills/plan-to-implementation-procedure/workflow.md`, `skills/plan-to-implementation-procedure/workflow-edge.md`, `tools/check_skill_size_baseline.txt`
