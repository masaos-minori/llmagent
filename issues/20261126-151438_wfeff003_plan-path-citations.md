# Make Plan path citations machine-readable by default

## Priority
Medium

## Summary
Plans cite test paths and step file paths in plain text, but the tools that read them need backticked paths, so companion detection and the Plan step update fail silently. Make the backtick form the default at generation time and detect the plain form in the checker.

## Background
Evidence (`Explicit in code`, by reading and `rg`): `tools/backtick_plan_related_tests.py` already normalizes `Related Tests` cells to backticked paths (its row is in `tools/TOOL_DESCRIPTIONS.md`), but no file under `skills/`, `templates/`, or `rules/` mentions it. `tools/check_workitem_traceability.py` reads `Related Tests` cells through backticked paths and reports `companion-not-eligible` when they are plain. `tools/close_procedures_batch.py` reads a Plan step's cited files through a backtick regular expression (`_BACKTICKED`) and reports `cites no Implementation Target Files path (cannot map it)` otherwise. `templates/plan.md` does not say that these paths must be backticked.

Observed in one session: three Plans (the web search fetch boundary, the web search configuration and audit, and the dedup keyless gate) were generated with plain paths; the procedure phase found the problem only through a checker run and fixed the cells by hand, and `--plan-steps` could not map any Plan step afterward.

## Problem
Two tools silently disagree with how Plans are written, and the failure appears late, in a later phase.

## Reason for Change
Avoidable rework in every Plan and a manual Plan step update in every batch. Not urgent.

## Implementation Intent
Write backticked paths at Plan generation (template wording plus the existing normalizer extended to step citations), and make `tools/check_workitem_structure.py` report a plain path that equals a target row path.

## Target Files or Areas
- `templates/plan.md`
- `skills/issue-to-plan/workflow.md` (Step 5 and Step 8: run the normalizer before the structure check)
- `tools/backtick_plan_related_tests.py` (extend to `Implementation steps` citations or add a sibling mode)
- `tools/check_workitem_structure.py`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- State in `templates/plan.md` that paths in `Related Tests` cells and in `Implementation steps` are written in backticks.
- Extend the normalizer so a path equal to an `Implementation Target Files` row is backticked in the step list; keep it idempotent.
- Add a finding to `tools/check_workitem_structure.py` for a plain path in those two places, with exit code behavior consistent with the other Plan findings, and a baseline for archived Plans.
- Run the normalizer in `skills/issue-to-plan/workflow.md` before the structure check (Step 8a).

## Constraints
- Do not rewrite archived Plans; use a baseline as the other checkers do.
- The normalizer must not change any other text of the Plan.

## Acceptance Criteria
- [ ] A Plan generated with plain paths is corrected by the normalizer, and the structure checker then reports no such finding.
- [ ] `tools/close_procedures_batch.py --plan-steps` maps the steps of a normalized Plan.
- [ ] A plain-path Plan produces the new finding before the procedure phase.

## Testing Expectations
Unit tests for the normalizer on steps and cells (idempotence, no change elsewhere) and for the new finding; the existing checker tests; ruff, mypy; `tools/check_tool_descriptions_sync.py`.

## Documentation Impact
Yes. `templates/plan.md`, `tools/TOOL_DESCRIPTIONS.md`, and the Step 5 and Step 8 wording of `skills/issue-to-plan/workflow.md`.

## Out of Scope
- Changing how `close_procedures_batch.py` reads citations (it keeps requiring backticks).
- Archived Plans.

## Dependencies
- Blocks: issues/20261126-151441_wfeff006_finalize-procedure-checks.md (its coverage check relies on readable citations).

## Unresolved Questions
- `不明`: whether the normalizer should be extended or a second tool added.

## AI Implementation Instruction
Reuse the existing normalizer. Stop and report if a Plan layout exists where a path cannot be backticked without changing meaning.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261126-151438
- **Related target files**: `templates/plan.md`, `skills/issue-to-plan/workflow.md`, `tools/backtick_plan_related_tests.py`, `tools/check_workitem_structure.py`, `tools/TOOL_DESCRIPTIONS.md`
