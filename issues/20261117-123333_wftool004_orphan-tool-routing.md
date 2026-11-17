# Register under-referenced workflow tools in the routing and workflow steps

## Priority
Low

## Summary
`tools/audit_plan_target_paths.py` runs only inside `tools/amend_plan.py`, and `tools/sync_plan_workitem_status.py` appears in one workflow line and not in `routing.md`. Make both discoverable at the step where they apply.

## Background
Filed from the investigation of the issue -> plan -> implementation toolchain. Claims below were verified in this investigation by reading tool source, running `--help`, and `rg`, unless marked `Needs confirmation`.

## Problem
`audit_plan_target_paths.py` has no reference in `skills/` or `routing.md`; `amend_plan.py` calls it after a Plan is frozen (`Explicit in code`). `skills/issue-to-plan/workflow.md` Step 8b freezes the target files without naming a path audit. `sync_plan_workitem_status.py` is referenced once, in `skills/code-implementation/workflow.md`, and is absent from the `routing.md` table (`Explicit in code`).

## Reason for Change
- A Plan can be frozen with a nonexistent target path that only a later amendment audit would surface.
- An operator scanning the `routing.md` table does not find the Plan row reconciliation tool.
- Nothing makes this time-sensitive; the cost is small, and the benefit is discoverability.

## Implementation Intent
- Step 8b of `issue-to-plan` runs the path audit before the freeze.
- `routing.md` lists both tools with their trigger situation.
- The gate mapping derived from `routing.md` keeps passing the hook-parity drift check.

## Target Files or Areas
- `routing.md`
- skills/issue-to-plan/workflow.md (Step 8b)
- `skills/code-implementation/workflow.md`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Add the path audit to Step 8b with its fallback if the tool is unavailable.
- Add `routing.md` rows for the audit and the Plan row reconciliation, stating the triggering situation.
- Run `uv run python tools/run_validation_gates.py drift` to confirm the new routing rows map cleanly.

## Constraints
- Do not grow `tools/run_validation_gates.py`; the routing rows with runtime arguments are reported `Not available`, which is expected.
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- `skills/issue-to-plan/workflow.md` Step 8b names the path audit.
- `routing.md` has rows for both tools, and `run_validation_gates.py drift` passes.
- `tools/check_skills_references.py` and `tools/check_skills_heading_cycles.py` pass.

## Testing Expectations
Documentation-only plus the drift check; run the skills reference checkers listed in `routing.md`. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. `routing.md` and two workflow documents.

## Out of Scope
- Changing the behavior of either tool.
- Making the audit a blocking gate.

## Dependencies
- `issues/20261117-123335_wftool006_gate-output-noise.md` also changes how routing rows with runtime arguments appear in the gate output.

## Unresolved Questions
- N/A: none

## AI Implementation Instruction
- Keep each added sentence in the workflow documents to the trigger, the command, and the fallback.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-123333
- **Related target files**: `routing.md`; skills/issue-to-plan/workflow.md (Step 8b); `skills/code-implementation/workflow.md`; `tools/TOOL_DESCRIPTIONS.md`
