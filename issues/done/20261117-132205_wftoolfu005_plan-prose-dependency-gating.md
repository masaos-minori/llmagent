# Stop prose mentions of other plans from silently gating a plan

## Priority
Medium

## Summary
A Plan's free-text Dependencies line turns every `plans/` or `issues/` path in it into a dependency when the Plan has no structured `Depends on` line, while the template says sequencing notes belong in that prose line. Make the template, the workflow guidance, and the tool agree.

## Background
Found while generating the plans for the workflow tooling issues: the Plans `plans/20261117-124614_wftool002_status-vocabulary-unify.md` and `plans/20261117-125207_wftool004_orphan-tool-routing.md` were reported `gated (prose)` behind sibling Plans because the overlap notes in their Dependencies line named those Plans by path, although the overlaps had been judged compatible. The text was reworded before the Plans were committed.

## Problem
`tools/plan_dependency_order.py` reads a structured `**Depends on**` bullet and, when none exists, treats every `plans/` or `issues/` path in the `- **Dependencies**:` bullet as a dependency with phase `all` (`Explicit in code`, module docstring and `parse_dependencies`). `templates/plan.md` tells the author that sequencing-only notes stay in the prose line (`Explicit in code`). `skills/issue-to-plan/workflow.md` Step 8b tells the author to add a sequencing dependency's Plan to the Scope Dependencies (`Explicit in code`). A prose mention written to say "no ordering" therefore creates a hard gate (`Operationally observed`: two of the six Plans written in one session). The tool computes a `prose-dependency` warning for each such path; whether the default output shows it is `Needs confirmation`.

## Reason for Change
- A false gate marks the Plan's procedures `Gated:` and makes `code-implementation` report the Plan as gated, which stalls work that has no real prerequisite.
- The template, the workflow, and the tool each give a different rule, so any author following the template can trigger it.
- It was caught here only because the order was inspected by hand. The cost of a wrong gate is a stalled implementation, not data loss.

## Implementation Intent
- One rule is stated the same way in the template, the issue-to-plan workflow, and the tool description: real ordering goes in a structured `Depends on` line, and prose names other Plans by title.
- Either the guidance tells authors not to write other Plans' paths in the prose line, or the tool stops treating prose paths as gates and only warns; the choice is made once and applied everywhere.

## Target Files or Areas
- `templates/plan.md`
- skills/issue-to-plan/workflow.md (Step 8b)
- `tools/plan_dependency_order.py`
- `tests/tools/test_plan_dependency_order.py`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Decide between guidance-only and a tool change (prose paths warn but do not gate).
- Apply the decision to the template note, the workflow step, and the tool description; if the tool changes, update its docstring and tests.
- Confirm whether the `prose-dependency` warning reaches the default output, and make it visible if it does not.
- Add tests for the chosen behavior with a Plan that has only a prose mention.

## Constraints
- Do not change the structured `Depends on` semantics or the closed/open rules.
- Overlap notes (shared target files) remain report-only and never ordering edges.
- Follow `routing.md` Tools, section "Adding a new tool", for every changed `tools/*.py`: ruff format and check, mypy, bandit, a smoke run against real repository data, and `tools/TOOL_DESCRIPTIONS.md` sync (`tools/check_tool_descriptions_sync.py`).
- Respect the `tools/` module-size gate (`tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt`): the baseline only shrinks, so a tool at or over the limit MUST NOT grow; put new logic in a new module instead.
- Follow the tool CLI conventions recorded in `tools/TOOL_DESCRIPTIONS.md`: exit codes `0` pass, `1` findings, `2` usage or environment error; `--dry-run` and atomic writes for tools that rewrite files.
- Follow the Current-Specification-Only policy: no aliases, shims, or history-style comments for removed behavior.
- Keep code comments, log text, and documentation in English; change only the Target Files and report any other needed file as a scope amendment.

## Acceptance Criteria
- The template, the workflow, and the tool description state the same rule (review).
- A Plan that names another Plan only in prose is `ready` or shows a visible warning, according to the decision (test).
- A structured `Depends on` line still gates the Plan (test).
- `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, and `tools/check_tool_descriptions_sync.py` pass.

## Testing Expectations
Unit tests under `tests/tools/test_plan_dependency_order.py`; a run over the live Plans before and after; ruff, mypy, bandit. Validation sequence: `rules/toolchain.md`; after any `docs/` edit also the checkers listed in `routing.md` Tools.

## Documentation Impact
Yes. `templates/plan.md`, `skills/issue-to-plan/workflow.md`, and the tool description.

## Out of Scope
- Changing how overlaps are reported.
- Adding new dependency kinds.

## Dependencies
- `plans/20261117-125207_wftool004_orphan-tool-routing.md` also edits `skills/issue-to-plan/workflow.md` (Step 8b and the Toolchain paragraph): follows its phase 3 so both edits land in the same section in order.

## Unresolved Questions
- Whether the default output shows the `prose-dependency` warning is `Needs confirmation`.
- Which of guidance-only and a tool change the maintainer prefers is `不明`.

## AI Implementation Instruction
- Present the two options with the observed failure and stop before implementing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261117-132205
- **Related target files**: `templates/plan.md`; skills/issue-to-plan/workflow.md (Step 8b); `tools/plan_dependency_order.py`; `tests/tools/test_plan_dependency_order.py`; `tools/TOOL_DESCRIPTIONS.md`
