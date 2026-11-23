# Finish the staged compression of the pipeline skill workflows (Stages B to F)

## Priority
Low

## Summary
Continue the staged compression after Stage A (the main-path and edge-case split of `code-implementation`, planned in `plans/20261123-161734_skillsize002_compress-skill-workflows-structure.md`): the same split for `plan-to-implementation-procedure` and `issue-to-plan`, thinner `SKILL.md` files, condensed manual-fallback prose, and two optional stages (preflight and postflight tools, selective loading of the shared rules). Each stage is justified by its measured saving; the later stages are optional.

## Background
Parent issues: `issues/done/20261123-155457_skillsize001_compress-skill-workflows.md` (Stages 1 and 2, implemented in `1e916038e`) and `issues/20261123-155940_skillsize002_compress-skill-workflows-structure.md` (its adversarial verification and Stage A plan). The measurements are recorded in the skillsize002 issue and plan: repeated per-invocation cost is dominated by the workflow, the `SKILL.md`, and the prompt (shared rules are read once per session); `code-implementation` is 52 KB + 6.5 KB + 3 KB, `plan-to-implementation-procedure` 39 KB + 7 KB + 3 KB, `issue-to-plan` 46 KB + 10.5 KB + 6 KB. Realistic savings per stage, from the section sizes: Stage A about 10.5 KB for `code-implementation`; Stage B about 3 KB each for `plan-to-implementation-procedure` (non-conforming plan, gated, plan amendment text) and `issue-to-plan` (existing-Plan, re-entry, no-Plan cases; Path B is already a separate file); Stage C (thinner `SKILL.md`) 2 KB to 4 KB per skill; Stage D (condensed fallback prose) 3 KB to 5 KB per skill but it rewords; Stage E (preflight and postflight tools) under 1 KB of text per skill; Stage F (selective loading) matters only after compactions and in fresh sessions.

## Problem
After Stages 1, 2, and A, `plan-to-implementation-procedure` and `issue-to-plan` still read about 49 KB and 62 KB of workflow, `SKILL.md`, and prompt at each invocation, and the achievable further saving is small per stage, so each remaining stage needs its own cost and benefit check.

## Reason for Change
Not time-sensitive: the largest saving (Stage A) is planned; the rest should follow only if the measured benefit justifies the risk of moving or rewording rule text.

## Implementation Intent
Run the stages in this order, one skill per change, and decide at each step from the measured numbers whether the next stage is worth doing.
- Stage B: split `plan-to-implementation-procedure/workflow.md` and `issue-to-plan/workflow.md` into a main path and an edge-case file with trigger lines, moving text verbatim, as Stage A does for `code-implementation`.
- Stage C: reduce each pipeline `SKILL.md` to its description, phase table, and references; every Core Rule stays in `workflow.md`.
- Stage D: condense the detailed manual-fallback prose of tool-covered steps to the tool command, the checklist, and a one-line fallback; this stage rewords, so it needs the maintainer's go-ahead after B and C are measured.
- Stage E (optional): preflight and postflight tools for the repeated verification sequence.
- Stage F (optional): a section-reading convention for the shared rules.

## Target Files or Areas
- `skills/plan-to-implementation-procedure/`, `skills/issue-to-plan/`, `skills/issue-creator/`, `skills/git-commit-and-sync/`, `skills/code-implementation/SKILL.md` (`SKILL.md`, `workflow.md`, new edge-case files)
- `prompts/01_issue-to-plan.md`, `prompts/02_plan-to-implementation-procedure.md`, `templates/plan.md` and other files that cite a moved section
- For Stages E and F only: `tools/` (new tools and tests), `tools/TOOL_DESCRIPTIONS.md`, `tools/_validation_gate_defs.py`, `rules/ai-execution.md`, `rules/workflow-lifecycle.md`
- `tools/check_skill_size_baseline.txt` after every stage

## Required Changes
- Stage B: create one edge-case file per skill with the conditional sections verbatim, add one trigger line per moved section, update outside citations found by a repository scan, and lower the baseline.
- Stage C: shrink each `SKILL.md` as described, with no rule lost (a Core Rule is added to `workflow.md` first if absent).
- Stage D, E, F: only after the maintainer confirms the benefit; each is its own Plan.
- After each stage: re-measure the repeated load, lower the baseline with `tools/check_skill_size.py --update-baseline`, and record the numbers in the stage's commit message.

## Constraints
- No normative rule changes meaning, is weakened, or is dropped; moving text is allowed, and rewording is limited to Stage D. Every moved `MUST` or `MUST NOT` stays discoverable from a trigger line (checked by a before and after extraction of the normative sentences).
- Each stage is its own change and passes `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py` (trigger lines carry no resolvable section name), `tools/check_workitem_structure.py`, the documentation checkers, and the size-budget check before the next stage starts.
- Do not rename or remove files cited from many documents; keep every heading of a moved section in the main workflow so citations by section name stay valid.
- Run a stage while no other session edits `skills/`, `rules/`, `prompts/`, or `templates/`, and commit and push it before starting the next.

## Acceptance Criteria
- After each stage, the repeated load of the skill it touched is lower by the amount its plan states, measured with the method of `skillsize001`.
- At the end, the repeated load of `plan-to-implementation-procedure` and `issue-to-plan` is at least 15 percent lower than the 2026-11-23 figures, counting Stages 1, 2, and B (and C if done).
- Every `MUST` and `MUST NOT` of the original files can be found in the main path or in a named edge-case file reachable from a trigger line.
- The size-budget check, the reference and heading-cycle checks, the structure checker, the documentation checkers, and `tools/run_validation_gates.py` pass after each stage.

## Testing Expectations
- The reference, heading-cycle, size-budget, and gate checks after each stage; the full test suite after a stage that touches `tools/`.
- A before and after extraction of the normative sentences for each split file, kept as evidence in the stage's procedure.
- For Stages E and F: unit tests for each new tool, including failure cases.

## Documentation Impact
Yes: the skills, prompts, and templates named above change; each stage records where its moved sections went. No ADR and no `docs/*.md` change.

## Out of Scope
- Changing the meaning of any pipeline rule or the required sections of the issue, plan, and procedure templates.
- Skills outside the five pipeline skills, except where they cite a moved section.
- Changing harness behavior (how a skill is loaded or compacted).

## Dependencies
- Depends on `plans/20261123-161734_skillsize002_compress-skill-workflows-structure.md` (Stage A) being implemented first: this issue starts from its recorded numbers and uses its split pattern. Order: that Plan, then this issue.
- Related: `issues/20261123-155940_skillsize002_compress-skill-workflows-structure.md` (the parent issue; its verification and Stage A plan).
- Sibling check (2026-11-23): no other open issue or plan targets the skill, prompt, or template files named here.

## Unresolved Questions
- `不明`: how often each edge-case section is exercised in real runs (read from the workflows, not counted from transcripts); Stage B's boundaries should be checked against recent run transcripts if a count becomes available.
- `不明`: whether the maintainer wants Stages D, E, and F at all if B and C reach the target; D rewords and E saves little text.
- `不明`: the real token cost of one invocation (the estimate divides bytes by four).

## AI Implementation Instruction
Plan and implement one stage at a time, in order, and stop after each stage to compare the measured saving with the estimate before starting the next. Move text, do not reword it, except in Stage D after the maintainer agrees. Keep every `MUST` and `MUST NOT`, keep every moved section's heading in the main workflow, and keep trigger lines free of resolvable section names. Do not start a stage while another session edits the same files, and do not start before Stage A is implemented.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261123-161734_skillsize002_compress-skill-workflows-structure.md`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-161834
- **Related target files**: `skills/plan-to-implementation-procedure/`, `skills/issue-to-plan/`, `skills/issue-creator/`, `skills/git-commit-and-sync/`, `skills/code-implementation/SKILL.md`, `prompts/01_issue-to-plan.md`, `prompts/02_plan-to-implementation-procedure.md`, `templates/plan.md`, `tools/check_skill_size_baseline.txt`
