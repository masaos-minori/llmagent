# Generate the mechanical columns of the Plan Affected areas table

## Priority
Low

## Summary
Add a tool that computes the mechanical columns of a Plan's `Affected areas` table (change type, 30-day churn, bus factor, module size headroom, `deploy.sh` impact) from the target rows, so the author fills only the judgment column (`Blast Radius`).

## Background
Evidence (`Explicit in code`): `templates/plan.md` defines six columns for every `Implementation Target Files` row. `skills/issue-to-plan/workflow-path-b.md` "Historical analysis" gives a `git log` command and mentions `git-fame` for bus factor. `tools/amend_plan.py` already finds and edits the `## Affected areas` section. In one session the values were collected by hand with `git log --since=30.days` and `git shortlog` loops, and one `git shortlog -sn -- <file>` call blocked reading standard input because it had no revision argument when not run on a terminal.

## Problem
Collecting these values is repetitive and error-prone, and the manual commands have a pitfall.

## Reason for Change
Token and time cost on every Path B Plan; no correctness risk. Low urgency.

## Implementation Intent
A read-only tool that prints the six-column rows for a Plan's target files, deterministic and reproducible, leaving `Blast Radius` as a marked placeholder for the author.

## Target Files or Areas
- `tools/fill_affected_areas.py` (new)
- `tools/TOOL_DESCRIPTIONS.md`
- `skills/issue-to-plan/workflow-path-b.md` and `skills/issue-to-plan/workflow.md` (Step 5 reference to the tool)

## Required Changes
- Read the Plan's target rows and print or insert `Affected areas` rows: `Change` from the row's Change Responsibility, `Churn (30d)` from git history, `Bus Factor` by one documented rule, module size against the 24576 B gate, and `deploy.sh Impact` from `rules/env.md`.
- Mark a created file `N/A (new)` for churn and bus factor.
- Run every git command with standard input closed.
- Verify on three existing Plans that the output equals the hand-computed values.

## Constraints
- Read-only unless an explicit insert flag is given; never change other Plan sections.
- The tool must not guess `Blast Radius`.

## Acceptance Criteria
- [ ] Output rows match the manual commands on the three sample Plans.
- [ ] A new file and a deleted file are handled.
- [ ] The tool does not hang when standard input is not a terminal.

## Testing Expectations
Unit tests on a temporary git repository; ruff, mypy, bandit; `tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. The tool row and the two skill references.

## Out of Scope
- Computing blast radius or dependency graphs.

## Dependencies
- N/A: none

## Unresolved Questions
- `不明`: the bus factor rule (author count, or the more than 70 percent single-author rule named in `workflow-path-b.md`).

## AI Implementation Instruction
Reuse the section parsing of `tools/amend_plan.py`. Stop and report if the two bus factor rules disagree on the sample Plans.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151440
- **Related target files**: `tools/fill_affected_areas.py`, `tools/TOOL_DESCRIPTIONS.md`, `skills/issue-to-plan/workflow-path-b.md`, `skills/issue-to-plan/workflow.md`
