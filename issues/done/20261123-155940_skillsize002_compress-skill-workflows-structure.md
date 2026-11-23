# Compress the pipeline skill workflows structurally (Stages 3 to 7 of skillsize001)

## Priority
Medium

## Summary
Continue the staged compression of the issue-to-plan-to-implementation skill workflows after the size-budget gate and the runtime split of `skills/DESIGN.md` are in place: thinner `SKILL.md` files, one preflight and one postflight tool per pipeline phase, a main-path and edge-case split of each workflow, condensed manual-fallback prose, and a section index for the shared rules. Every normative rule must survive each move.

## Background
This is the follow-up of `issues/20261123-155457_skillsize001_compress-skill-workflows.md` (Stages 1 and 2 are planned in `plans/20261123-155813_skillsize001_compress-skill-workflows.md`). The measurements, the growth history, and the reasoning are recorded there: one pipeline invocation loads about 146 KB to 175 KB, the pipeline workflows and main rules grew from 92.6 KB (2026-09-01) to 232 KB (2026-11-23), and the bulk is conditional branches embedded in the main path plus per-incident accretion, not verbatim duplication. The largest sections are `plan-to-implementation-procedure` Step 3c (about 12 KB), `issue-to-plan` Step 5 (about 9.8 KB), and `code-implementation` Step 4, Step 7, and the Plan Execution Status update (3.7 KB to 4.8 KB each). Most steps already have tools, yet the workflows keep a detailed manual fallback and a hand-listed verification sequence (structure check, stale detector, dependency order, overlaps, plan coverage, gates). `issue-to-plan/workflow-path-b.md` is the existing precedent for a conditional file loaded only when its trigger holds.

Stages 1 and 2 give this issue its tools: the size-budget check (`tools/check_skill_size.py`, with a baseline) makes every reduction below measurable and prevents regrowth, and `rules/skill-runtime.md` already moved the runtime sections of `skills/DESIGN.md`.

Adversarial verification (2026-11-23, measured after Stages 1 and 2 landed in `1e916038e`) corrected the first estimates of this issue:
- **Where the bytes are.** For a fresh `plan-to-implementation-procedure` cycle (152 KB after Stage 2) the workflow is 39 KB and the `SKILL.md` 7 KB; the rest is shared files loaded once per session and reused (`rules/ai-execution.md` 17 KB, `rules/toolchain.md` 14 KB, `routing.md` 12.7 KB, `rules/workflow-lifecycle.md` 12.5 KB, `rules/coding.md` 9.5 KB, templates 27 KB). Within one session the shared files are read once (Step 0 loads a file only if it is not already loaded), while the workflow, the `SKILL.md`, and the prompt are read again at every invocation and after every context compaction. Repeated cost is therefore dominated by the workflow files: `code-implementation` 52 KB + 6.5 KB + 3 KB, `plan-to-implementation-procedure` 39 KB + 7 KB + 3 KB, `issue-to-plan` 46 KB + 10.5 KB + 6 KB.
- **Stage 4 (preflight and postflight tools) is overstated.** The hand-listed verification commands occupy 0.6 KB to 0.9 KB per workflow (7 to 10 lines), so the tools would save under 1 KB of text per skill; their value is fewer commands per cycle, not bytes. It should be optional and last.
- **Stage 5 (main-path and edge-case split) is smaller than estimated.** The truly conditional sections are about 9 KB in `code-implementation` (batch mode for a plan 3.2 KB and for a release unit 2.1 KB, rollback 1.6 KB, the resume, superseded, and gated bullets of Step 1 about 2.8 KB, the manual path of the Plan Execution Status update about 1.6 KB), about 3 KB in `plan-to-implementation-procedure`, and about 3 KB in `issue-to-plan` (Path B is already a separate file). The 25 KB to 40 KB per cycle first assumed is not reachable by splitting alone.
- **Stage 3 (thinner `SKILL.md`)** saves 2 KB to 4 KB per skill: each has a phase table of 5 to 11 rows that paraphrases the workflow, but only one verbatim duplicate sentence exists across all five skills and the shared rules.
- **Stage 7 (selective loading of shared rules)** saves little in a session because shared files are already read once; it matters only after compactions and for a fresh session, and it needs a section-reading convention, so it moves to the end.
- Realistic total with Stages 1 and 2 (about 9 percent, done): about 20 to 25 percent for `code-implementation` and 15 to 20 percent for the other two once Stages 3 and 5 are done. The 30 percent acceptance target below is lowered accordingly.
- Moved sections are cited almost only from inside their own workflow (the exception is `prompts/03_implementation.md` citing `Rollback on Failure`), so a split needs few reference updates; keep cross-file references plain (a backticked path without a section name creates no edge for `tools/check_skills_heading_cycles.py`).

## Problem
After Stages 1 and 2 the per-invocation load is still about 130 KB to 160 KB: the workflows are long because rarely used branches and tool-covered fallbacks sit in the main path, every cycle repeats the same verification commands by hand, and each `SKILL.md` restates content that `workflow.md` already holds.

## Reason for Change
Context compactions during long pipeline runs force the workflows to be re-read, which multiplies the cost, and the structure above makes each re-read large. The structural stages are the larger saving (about 25 to 40 KB per ordinary cycle) but also the riskier ones, so they follow the measured baseline instead of being bundled with it.

## Implementation Intent
Stage the work one skill at a time, in the order of repeated cost, and re-measure after each stage with `tools/check_skill_size.py`. Revised order after the verification above:
- Stage A (first plan): split `code-implementation/workflow.md` into the main path and `workflow-edge.md` (batch modes, rollback, the resume, superseded, and gated bullets of Step 1, the manual path of the Plan Execution Status update), with one trigger line per moved section and the baseline lowered. Move text verbatim; keep every `MUST` and `MUST NOT`.
- Stage B: the same split for `plan-to-implementation-procedure` and `issue-to-plan`.
- Stage C: reduce each `SKILL.md` to its description, phase table, and references (Core Rules stay in `workflow.md`).
- Stage D: condense the detailed manual-fallback prose of steps already covered by tools (archival moves, status updates, scaffolding) to the tool command, the checklist, and a one-line fallback; this is the only stage that rewords, so it follows the measured effect of A to C and needs the maintainer's go-ahead.
- Stage E (optional): preflight and postflight tools for the repeated verification sequence; low text value, keep only if the maintainer wants fewer commands per cycle.
- Stage F (optional): a section-reading convention for the shared rules (index of `rules/ai-execution.md`, selective Step 0 loading), useful after compactions and for fresh sessions.
- Target (estimate, re-measured per stage): about 20 to 25 percent below the 2026-11-23 repeated load for `code-implementation` and 15 to 20 percent for the other two pipeline skills, counting Stages 1 and 2.

## Target Files or Areas
- `skills/issue-creator/`, `skills/issue-to-plan/`, `skills/plan-to-implementation-procedure/`, `skills/code-implementation/`, `skills/git-commit-and-sync/` (`SKILL.md`, `workflow.md`, new edge-case files)
- `rules/ai-execution.md`, `rules/workflow-lifecycle.md`, `rules/tool-gates.md`, `routing.md`, `prompts/01_*`, `prompts/02_*`, `prompts/03_*`
- New preflight and postflight tools under `tools/` with tests under `tests/tools/`, `tools/TOOL_DESCRIPTIONS.md`, `tools/_validation_gate_defs.py`, `.github/workflows/ci.yml`, and the size baseline `tools/check_skill_size_baseline.txt`

## Required Changes
- Stage A: split `skills/code-implementation/workflow.md` into the main path and `workflow-edge.md`, with a trigger line per moved section, `prompts/03_implementation.md` updated for the moved Rollback section, and the size baseline lowered.
- Stage B: the same split for `skills/plan-to-implementation-procedure/workflow.md` and `skills/issue-to-plan/workflow.md`.
- Stage C: shrink each pipeline `SKILL.md` as described, with no rule lost.
- Stage D: condense the manual-fallback prose of tool-covered steps, one skill per change, after the maintainer agrees.
- Stage E (optional): implement the preflight and postflight tools, their tests, and the registrations, and replace the hand-listed sequences.
- Stage F (optional): add the section indexes and the selective Step 0 loading.
- After each stage: re-measure the repeated load, lower the baseline with `tools/check_skill_size.py --update-baseline`, and record the numbers in the stage's commit message.

## Constraints
- No normative rule changes meaning, is weakened, or is dropped. Moving text is allowed; rewording is limited to what the move requires, and every moved `MUST` or `MUST NOT` stays discoverable from the main path through a trigger line or a reference.
- Each stage is its own change (and its own Plan if the stage's rows can be frozen separately) and passes `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/check_workitem_structure.py`, the documentation checkers, and the size-budget check before the next stage starts.
- The five skills and their prompts must keep working after every stage; a stage must not leave a skill half-split.
- Do not rename or remove files cited from many documents (`skills/DESIGN.md`, `rules/ai-execution.md`); add files and change references instead.
- New tools follow `routing.md` "Adding a new tool" and `rules/tool-gates.md` registration and must not weaken an existing gate.
- Run a stage while no other session edits `skills/` or `rules/`, and commit and push it before starting the next.

## Acceptance Criteria
- After each stage, the repeated load (workflow, `SKILL.md`, and prompt) of the skill it touched is lower by the amount the stage's plan states, measured with the method of `skillsize001`; the final numbers are recorded in the closing change.
- At the end, the repeated load of `code-implementation` is at least 20 percent lower, and of `plan-to-implementation-procedure` and `issue-to-plan` at least 15 percent lower, than the 2026-11-23 figures, counting Stages 1 and 2.
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
- Stages 1 and 2 of the parent issue are implemented (`plans/done/20261123-155813_skillsize001_compress-skill-workflows.md`, commit `1e916038e`): the size-budget check, its baseline, and `rules/skill-runtime.md` exist, so this dependency is closed.
- Related: `issues/done/20261123-155457_skillsize001_compress-skill-workflows.md` (the parent issue).
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
