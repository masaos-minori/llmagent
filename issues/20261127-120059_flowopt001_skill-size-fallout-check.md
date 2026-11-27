# Add skill size ceilings to the issue-to-plan predictable fallout check

## Priority
Medium

## Summary
Make the issue-to-plan predictable fallout check name the skill size ceilings, and let `tools/check_skill_size.py` print the headroom of given files, so a Plan never freezes a skill edit that cannot fit.

## Background
Evidence (`Explicit in code`): `skills/issue-to-plan/workflow-edge.md` section "Step 3: predictable fallout check" lists module size (`scripts/` or `tools/`), pinned counts, tool inventory, and generated blocks, but not the skill size gate of `tools/check_skill_size.py`. `tools/check_skill_size_baseline.txt` records ceilings that equal or nearly equal the current size of the pipeline workflows. In the 2026-11-27 session the Plans for wfeff006, wfeff007, and wfeff009 each had to be redesigned around `skills/*/workflow.md` headroom of 0 to 23 B (move text to an edge file, order the Plans, size the replacement text). `tools/check_skill_size.py` has `--top`, `--limit`, `--baseline`, `--no-baseline`, `--update-baseline`, and `--root`, and no option that reports the headroom of a named file.

## Problem
The headroom of a skill file is found late (during Step 3 or after freeze) by hand with `wc -c` and the baseline file.

## Reason for Change
Each late discovery costs a Plan correction and a procedure rewrite; no correctness risk, but repeated.

## Implementation Intent
Add a fallout item for skill, rule, prompt, and template files that gain text, and add a read-only headroom report to the existing checker. Do not change what the size gate enforces.

## Target Files or Areas
- `skills/issue-to-plan/workflow-edge.md`
- `tools/check_skill_size.py`
- `tests/tools/test_check_skill_size.py`
- `tools/TOOL_DESCRIPTIONS.md`

## Required Changes
- Add to "Step 3: predictable fallout check" an item: for a covered instruction file (`skills/`, `rules/`, `prompts/`, `templates/`) that gains text, record its size, its ceiling (baseline entry or the 16384 B limit), and the headroom; when the planned growth exceeds the headroom, the Plan states where the text moves (an edge file row) or what it replaces.
- Add `--headroom PATH [PATH ...]` to `tools/check_skill_size.py`: for each path print size, ceiling, and headroom (negative means over); read-only; the exit code and the default output are unchanged.
- Document the option in the tool row.

## Constraints
- Default output and exit codes of `tools/check_skill_size.py` are unchanged.
- The size gate itself and its baseline semantics are not changed.
- `skills/issue-to-plan/workflow-edge.md` stays under 16384 B.

## Acceptance Criteria
- [ ] The fallout check names the skill size ceilings and what the Plan must record.
- [ ] `check_skill_size.py --headroom skills/issue-to-plan/workflow.md` prints size, ceiling, and headroom.
- [ ] The existing tests of the checker pass and the default output is unchanged.

## Testing Expectations
Unit tests for `--headroom` (under the limit, baselined, over the ceiling, unknown path); ruff, mypy, bandit; `tools/check_tool_descriptions_sync.py`; `tools/check_skill_size.py` and `tools/check_skills_references.py`.

## Documentation Impact
Yes. The fallout item in `skills/issue-to-plan/workflow-edge.md` and the `tools/TOOL_DESCRIPTIONS.md` row.

## Out of Scope
- Raising or lowering any ceiling.
- Moving text out of other skills.

## Dependencies
N/A: none

## Unresolved Questions
- `不明`: whether `--headroom` should also warn when a ceiling is within a given margin (not required here).

## AI Implementation Instruction
Keep the change to the fallout text, the option, and its tests. Do not alter the gate logic.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261127-120059
- **Related target files**: `skills/issue-to-plan/workflow-edge.md`, `tools/check_skill_size.py`, `tests/tools/test_check_skill_size.py`, `tools/TOOL_DESCRIPTIONS.md`
