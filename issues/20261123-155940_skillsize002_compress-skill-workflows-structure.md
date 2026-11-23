# Compress the pipeline skill workflows structurally (Stages 3 to 7 of skillsize001)

## Priority
Medium

## Summary
Continue the staged compression of the issue-to-plan-to-implementation skill workflows after the size-budget gate and the runtime split of `skills/DESIGN.md` are in place: thinner `SKILL.md` files, one preflight and one postflight tool per pipeline phase, a main-path and edge-case split of each workflow, condensed manual-fallback prose, and a section index for the shared rules. Every normative rule must survive each move.

## Background
This is the follow-up of `issues/20261123-155457_skillsize001_compress-skill-workflows.md` (Stages 1 and 2 are planned in `plans/20261123-155813_skillsize001_compress-skill-workflows.md`). The measurements, the growth history, and the reasoning are recorded there: one pipeline invocation loads about 146 KB to 175 KB, the pipeline workflows and main rules grew from 92.6 KB (2026-09-01) to 232 KB (2026-11-23), and the bulk is conditional branches embedded in the main path plus per-incident accretion, not verbatim duplication. The largest sections are `plan-to-implementation-procedure` Step 3c (about 12 KB), `issue-to-plan` Step 5 (about 9.8 KB), and `code-implementation` Step 4, Step 7, and the Plan Execution Status update (3.7 KB to 4.8 KB each). Most steps already have tools, yet the workflows keep a detailed manual fallback and a hand-listed verification sequence (structure check, stale detector, dependency order, overlaps, plan coverage, gates). `issue-to-plan/workflow-path-b.md` is the existing precedent for a conditional file loaded only when its trigger holds.

Stages 1 and 2 give this issue its tools: the size-budget check (`tools/check_skill_size.py`, with a baseline) makes every reduction below measurable and prevents regrowth, and `rules/skill-runtime.md` already moved the runtime sections of `skills/DESIGN.md`.

## Problem
After Stages 1 and 2 the per-invocation load is still about 130 KB to 160 KB: the workflows are long because rarely used branches and tool-covered fallbacks sit in the main path, every cycle repeats the same verification commands by hand, and each `SKILL.md` restates content that `workflow.md` already holds.

## Reason for Change
Context compactions during long pipeline runs force the workflows to be re-read, which multiplies the cost, and the structure above makes each re-read large. The structural stages are the larger saving (about 25 to 40 KB per ordinary cycle) but also the riskier ones, so they follow the measured baseline instead of being bundled with it.

## Implementation Intent
Stage the work one skill at a time, lowest risk first, and re-measure after each stage with the Stage 1 tool.
- Stage 3: reduce each `SKILL.md` to its description, phase table, and references; every Core Rule stays in `workflow.md` (added there first if absent).
- Stage 4: add one preflight and one postflight tool per pipeline phase that run the repeated verification sequence in the documented order and print one result (structure, stale detection, overlaps, dependency order, plan coverage, gates), then replace the hand-listed sequences with the tool call.
- Stage 5: split each `workflow.md` into a main path and an edge-case file loaded only when its trigger holds (batch mode, release unit, resume, superseded, gated, non-conforming plan, plan amendment, rollback); each main-path step names the trigger in one line. Order: `code-implementation`, `plan-to-implementation-procedure`, `issue-to-plan`, then `issue-creator` and `git-commit-and-sync` if their size warrants it.
- Stage 6: replace the detailed manual-fallback prose of steps already covered by tools (archival moves, status updates, scaffolding, plan updates) with the tool command, the verification checklist, and a one-line fallback; `tools/TOOL_DESCRIPTIONS.md` stays the single place for tool usage.
- Stage 7: give `rules/ai-execution.md` (and `rules/workflow-lifecycle.md` if worthwhile) a section index so a skill's Step 0 loads only the cited sections; make `rules/tool-gates.md` lookups defer to `run_validation_gates.py` output.
- Target after all stages (estimate, re-measured at the end): an ordinary single-procedure cycle loads about 100 KB (about 25k tokens) or less, 30 to 40 percent below the 2026-11-23 figures.

## Target Files or Areas
- `skills/issue-creator/`, `skills/issue-to-plan/`, `skills/plan-to-implementation-procedure/`, `skills/code-implementation/`, `skills/git-commit-and-sync/` (`SKILL.md`, `workflow.md`, new edge-case files)
- `rules/ai-execution.md`, `rules/workflow-lifecycle.md`, `rules/tool-gates.md`, `routing.md`, `prompts/01_*`, `prompts/02_*`, `prompts/03_*`
- New preflight and postflight tools under `tools/` with tests under `tests/tools/`, `tools/TOOL_DESCRIPTIONS.md`, `tools/_validation_gate_defs.py`, `.github/workflows/ci.yml`, and the size baseline `tools/check_skill_size_baseline.txt`

## Required Changes
- Stage 3: shrink each `SKILL.md` as described, with no rule lost.
- Stage 4: implement the preflight and postflight tools (read-only except where an existing tool already writes), their tests, and the tool and gate registrations; replace the hand-listed sequences.
- Stage 5: split the workflows one skill per change, add the trigger line to each main-path step, and keep every reference checker green.
- Stage 6: condense the manual-fallback prose one skill per change.
- Stage 7: add the section indexes and the selective Step 0 loading; update the cited anchors.
- After each stage: re-measure the per-invocation load, lower the recorded baselines with `tools/check_skill_size.py --update-baseline`, and record the numbers in the stage's commit message.

## Constraints
- No normative rule changes meaning, is weakened, or is dropped. Moving text is allowed; rewording is limited to what the move requires, and every moved `MUST` or `MUST NOT` stays discoverable from the main path through a trigger line or a reference.
- Each stage is its own change (and its own Plan if the stage's rows can be frozen separately) and passes `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/check_workitem_structure.py`, the documentation checkers, and the size-budget check before the next stage starts.
- The five skills and their prompts must keep working after every stage; a stage must not leave a skill half-split.
- Do not rename or remove files cited from many documents (`skills/DESIGN.md`, `rules/ai-execution.md`); add files and change references instead.
- New tools follow `routing.md` "Adding a new tool" and `rules/tool-gates.md` registration and must not weaken an existing gate.
- Run a stage while no other session edits `skills/` or `rules/`, and commit and push it before starting the next.

## Acceptance Criteria
- The per-invocation load measured with the Stage 1 method is at least 30 percent lower than the 2026-11-23 figures for `code-implementation`, `plan-to-implementation-procedure`, and `issue-to-plan`, with the final numbers recorded in the closing change.
- Every `MUST` and `MUST NOT` of the original skill and workflow files can be found in the main path or in a named edge-case file reachable from a trigger line (checked by a before and after extraction of the normative sentences, kept as evidence).
- The size-budget check, `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/check_workitem_structure.py`, the documentation checkers, and `tools/run_validation_gates.py` pass.
- A full cycle (issue, plan, procedure, implementation, commit) of a small change completes using only the new layout, without reading an edge-case file its trigger does not name.

## Testing Expectations
- Unit tests for each new tool (preflight, postflight) including failure cases (a stale procedure, a missing section, an uncovered row).
- The reference, heading-cycle, size-budget, and gate checks after each stage; the full test suite after each stage that touches `tools/`.
- A recorded before and after table of per-invocation load for the three measured skills.
- Manual verification: one end-to-end cycle on a small change after Stage 5 and again after Stage 7.

## Documentation Impact
Yes: the skills, rules, prompts, `routing.md`, `tools/TOOL_DESCRIPTIONS.md`, and `rules/tool-gates.md` change. The closing change records where each moved section went (a short map) and keeps `prompts/05_skills.md` guidance consistent. No ADR text and no `docs/*.md` change.

## Out of Scope
- Changing the meaning of any pipeline rule, the document workflow directories, or the required sections of the plan, procedure, and issue templates.
- Skills outside the five pipeline skills, except where they cite a moved section.
- Rewriting existing tools other than registering or calling them.
- Changing harness behavior (how a skill is loaded or compacted).

## Dependencies
- Depends on `plans/20261123-155813_skillsize001_compress-skill-workflows.md`: Stages 1 and 2 (the size-budget check and baseline, and `rules/skill-runtime.md`) must be implemented first; this issue starts from the figures recorded there. Order: that Plan first, then this issue.
- Related: `issues/20261123-155457_skillsize001_compress-skill-workflows.md` (the parent issue; its remaining stages are tracked here).
- Sibling check (2026-11-23): no other open issue or plan targets the skill, rule, or prompt files changed here.

## Unresolved Questions
- `不明`: the real token cost of one invocation (the estimate divides bytes by four); a tokenizer count would confirm the 30 percent target.
- `不明`: how often each edge-case section is exercised in real runs (the estimate that they are rare comes from reading the workflows, not from a transcript count); check Stage 5's split boundaries against recent run transcripts before it starts.
- `不明`: whether the maintainer wants Stages 6 and 7 at all if Stages 3 to 5 reach the target; they are the riskiest per byte saved.
- `不明`: whether `rules/ai-execution.md` should be split into several files or only indexed (Stage 7 assumes an index).
- `不明`: whether each stage gets its own Plan or whether Stages 3 and 4 share one (rows freeze separately only when their design is settled).

## AI Implementation Instruction
Implement one stage per plan, in the order above, and stop after each stage for a pipeline check before starting the next. Move text, do not reword it, and keep every `MUST` and `MUST NOT`. Do not rename files that other documents cite. Record before and after numbers for every stage, lower the size baseline after each reduction, and keep all reference, structure, and size checkers green at each commit. Do not start a stage while another session edits the same files, and do not start before the parent Plan's Stages 1 and 2 are implemented.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261123-155813_skillsize001_compress-skill-workflows.md`
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-155940
- **Related target files**: `skills/issue-creator/`, `skills/issue-to-plan/`, `skills/plan-to-implementation-procedure/`, `skills/code-implementation/`, `skills/git-commit-and-sync/`, `rules/ai-execution.md`, `rules/workflow-lifecycle.md`, `rules/tool-gates.md`, `routing.md`, `prompts/01_issue-to-plan.md`, `prompts/02_plan-to-implementation-procedure.md`, `prompts/03_implementation.md`, `tools/TOOL_DESCRIPTIONS.md`, `tools/_validation_gate_defs.py`, `tools/check_skill_size_baseline.txt`
