# Compress the issue-to-plan-to-implementation skill workflows in stages

## Priority
Medium

## Summary
The instructions that one pipeline cycle must load (skill, workflow, shared rules, templates) have grown to about 145 KB to 175 KB per invocation. Reduce them in stages, keeping every normative rule, by moving rare branches out of the main path, shrinking restated text, mechanizing repeated checks, and adding a size budget so the growth does not return.

## Background
Measured on 2026-11-23 (sizes in bytes; tokens are bytes divided by four, a rough estimate, not a tokenizer count):
- One invocation loads about 175 KB for `code-implementation` (workflow 52.6 KB, `rules/ai-execution.md` 17 KB, `rules/toolchain.md` 14.3 KB, `routing.md` 12.8 KB), about 167 KB for `plan-to-implementation-procedure` (workflow 39.1 KB, `skills/DESIGN.md` 18.9 KB), and about 146 KB for `issue-to-plan` (workflow 45.6 KB). The five pipeline skills together hold about 250 KB of `SKILL.md` and `workflow*.md`.
- Growth history (git, same files): the five workflows plus `rules/ai-execution.md`, `rules/workflow-lifecycle.md`, and `skills/DESIGN.md` were 92.6 KB on 2026-09-01, 157 KB on 2026-10-01, 202 KB on 2026-11-01, and 232 KB now. The `code-implementation` workflow went from 13 KB to 52.6 KB, `issue-to-plan` from 19 KB to 45.6 KB, `plan-to-implementation-procedure` from 15.8 KB to 39.1 KB. About 100 commits touched these files since 2026-10-01: the growth is accretion of per-incident rules, not one large addition.
- Verbatim duplication is small (one repeated sentence over 90 characters across the skill, rule, and DESIGN files). The bulk is structure: the largest sections are `plan-to-implementation-procedure` Step 3c (about 12 KB), `issue-to-plan` Step 5 (about 9.8 KB), and, in `code-implementation`, Step 4, Step 7, and the Plan Execution Status update (each 3.7 KB to 4.8 KB). Conditional branches (batch mode, release units, resume, superseded, gated, non-conforming plan, rollback, plan amendment) sit inside the main path.
- Most steps already have tools (`generate_workitem.py`, `amend_plan.py`, `close_procedures_batch.py`, `set_execution_status.py`, `manage_workitem_stage.py`, `run_validation_gates.py`) but the workflows still describe the manual fallback in detail, and the same four or five verification commands (structure check, stale detector, plan coverage, dependency order, gates) are listed by hand in every cycle.
- `skills/DESIGN.md` (18.9 KB, a design document for skill authors) is loaded by three skills for two short sections (Output language, Out-of-scope paths). `SKILL.md` restates the Phase overview and Core Rules that `workflow.md` already holds.
- Context compaction during long pipeline runs forces the workflows to be re-read, which multiplies the cost.
- Earlier consolidation work is archived (`issues/done/20260831-091832_skills05*`: it targeted restated explanatory text in `prompts/05_skills.md` and found little to remove), so this issue does not repeat it: the measured problem is branch embedding and accretion, not restatement.
- Existing guards that must stay green: `tools/check_skills_references.py` (referenced paths resolve), `tools/check_skills_heading_cycles.py`, `tools/check_workitem_structure.py`, `tools/check_docs_*` checkers, and the pre-commit hooks that run them. `skills/DESIGN.md` is referenced from many documents, so it cannot be renamed.

## Problem
Each cycle spends a large part of its context on instructions that mostly do not apply to the work at hand, and the files keep growing, which raises the cost of every run and the chance that a rule is missed or contradicted.

## Reason for Change
The pipeline is run many times per day and across context compactions; the per-invocation load has grown 2.5 times in three months. A budget and a main-path/edge-case split now are cheaper than after the next round of accretion.

## Implementation Intent
Stage the work from the lowest-risk, highest-return measures to the structural ones, one skill at a time, and do not change any rule's meaning while moving it.
- Stage 1: add a size-budget check with a recorded baseline (same model as `check_module_size.py`), so later stages can only reduce the baseline.
- Stage 2: extract the runtime parts of `skills/DESIGN.md` (Output language, Out-of-scope paths, and any other section the workflows cite for runtime behavior) into a small runtime rule file; keep `DESIGN.md` as the design document and point the skills at the small file.
- Stage 3: reduce each `SKILL.md` to its description, phase table, and references; the Core Rules stay in `workflow.md` only.
- Stage 4: add one preflight and one postflight tool per pipeline phase that run the repeated verification sequence in the documented order and print one result (structure, stale detection, overlaps, dependency order, plan coverage, gates), then replace the hand-listed command sequences with the tool call.
- Stage 5: split each `workflow.md` into a main path and an edge-case file loaded only when its trigger holds (batch mode, release unit, resume, superseded, gated, non-conforming plan, plan amendment, rollback). Each main-path step names the trigger in one line. `issue-to-plan/workflow-path-b.md` is the existing precedent.
- Stage 6: replace the detailed manual-fallback prose of steps already covered by tools (archival moves, status updates, scaffolding, plan updates) with the tool command, the verification checklist, and a one-line fallback; the tool descriptions in `tools/TOOL_DESCRIPTIONS.md` stay the single place for tool usage.
- Stage 7: give `rules/ai-execution.md` (and `rules/workflow-lifecycle.md` if worthwhile) a section index so a skill's Step 0 loads only the cited sections, and make `rules/tool-gates.md` lookups defer to `run_validation_gates.py` output.
- Target after all stages: an ordinary single-procedure cycle loads about 25k tokens (about 100 KB) or less, a reduction of 30 to 40 percent. This target is an estimate to be re-measured at the end of Stage 1.

## Target Files or Areas
- `skills/issue-creator/`, `skills/issue-to-plan/`, `skills/plan-to-implementation-procedure/`, `skills/code-implementation/`, `skills/git-commit-and-sync/` (`SKILL.md`, `workflow.md`, new edge-case files)
- `skills/DESIGN.md` and a new small runtime rule file
- `rules/ai-execution.md`, `rules/workflow-lifecycle.md`, `rules/tool-gates.md`, `routing.md`, `prompts/01_*`, `prompts/02_*`, `prompts/03_*`
- New tools under `tools/` (size-budget check, preflight/postflight) with tests under `tests/tools/`, `tools/TOOL_DESCRIPTIONS.md`, `tools/_validation_gate_defs.py`, `rules/tool-gates.md`, `.github/workflows/ci.yml` and `.pre-commit-config.yaml` for the new check

## Required Changes
- Stage 1: add the size-budget check, record per-file baselines for the skill, rule, prompt, and template files that pipeline cycles load, and wire it into the validation gates and CI.
- Stage 2: create the runtime rule file from the cited runtime sections of `skills/DESIGN.md`, update the Step 0 lists and references in every skill, and keep `skills/DESIGN.md` valid for its other readers.
- Stage 3: shrink each `SKILL.md` as described, with no rule lost (each Core Rule either exists in `workflow.md` or is added there first).
- Stage 4: implement the preflight and postflight tools (read-only except where an existing tool already writes), their tests, and the tool and gate registrations; replace the hand-listed sequences.
- Stage 5: split the workflows, one skill per change, in this order: `code-implementation`, `plan-to-implementation-procedure`, `issue-to-plan`, then `issue-creator` and `git-commit-and-sync` if their size warrants it; add the trigger line to each main-path step and keep every reference checker green.
- Stage 6: condense the manual-fallback prose as described, one skill per change.
- Stage 7: add the section indexes and the selective Step 0 loading; update the cited anchors.
- After each stage: re-measure the per-invocation load, lower the recorded baselines, and record the numbers in the stage's commit message.

## Constraints
- No normative rule changes meaning, is weakened, or is dropped. Moving text is allowed; rewording is limited to what the move requires, and every moved `MUST` or `MUST NOT` stays discoverable from the main path through a trigger line or a reference.
- Each stage is its own change and passes the existing reference, heading-cycle, structure, and docs checkers before the next stage starts.
- The five skills and their prompts must keep working after every stage (a pipeline cycle run against a small plan must complete), so stages must not leave a skill half-split.
- Do not rename or remove `skills/DESIGN.md`, `rules/ai-execution.md`, or other files cited from many documents; add files and change references instead.
- New tools follow `routing.md` "Adding a new tool" and `rules/tool-gates.md` registration, and must not weaken any existing gate.
- The measurement method (bytes divided by four) is an estimate; if a tokenizer count is available, use it for the final report, but do not change the targets based on it without recording why.

## Acceptance Criteria
- A size-budget check exists, passes on the final tree, and fails when a covered file grows beyond its recorded baseline without a recorded reason.
- The per-invocation load measured by the Stage 1 method is reduced by at least 30 percent for `code-implementation`, `plan-to-implementation-procedure`, and `issue-to-plan` relative to the 2026-11-23 numbers in Background, with the final numbers recorded in the closing change.
- Every `MUST` and `MUST NOT` of the original skill and workflow files can be found in the main path or in a named edge-case file reachable from a trigger line (checked by a before/after extraction of the normative sentences, kept as evidence).
- `tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/check_workitem_structure.py`, the documentation checkers, and `tools/run_validation_gates.py` pass.
- A full cycle (issue, plan, procedure, implementation, commit) of a small change completes using only the new layout, without reading an edge-case file that its trigger does not name.

## Testing Expectations
- Unit tests for each new tool (size budget, preflight, postflight) under `tests/tools/`, including the failure cases (growth over baseline, a stale procedure, a missing section).
- `uv run python tools/check_skills_references.py`, `tools/check_skills_heading_cycles.py`, `tools/run_validation_gates.py`, and the full test suite after each stage that touches `tools/`.
- A recorded before/after table of per-invocation load for the three measured skills.
- Manual verification: one end-to-end cycle on a small change after Stage 5, and again after Stage 7.

## Documentation Impact
Yes: the skills, rules, prompts, `routing.md`, `tools/TOOL_DESCRIPTIONS.md`, and `rules/tool-gates.md` change. The change must record where each moved section went (a short map in the closing change) and keep `prompts/05_skills.md` guidance consistent. No ADR text changes.

## Out of Scope
- Changing the meaning of any pipeline rule, the document workflow directories, or the plan, procedure, and issue templates' required sections.
- Skills outside the five pipeline skills (the `python-*` skills, `test-audit`, `deploy`), except where they cite a moved section.
- Rewriting the tools that already exist, other than registering or calling them.
- Changing harness behavior (how a skill is loaded or compacted).

## Dependencies
- Does not depend on an open issue or plan; sibling check (2026-11-23): the open issues and plans that mention `skills/` (`issues/20261119-145312_cliplc014_cli-docs-consolidation.md`, `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`, `plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md`, `plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md`) do not target the files this issue changes.
- Edits to the same skill files by pipeline runs in other sessions are a conflict risk: run each stage while no other session is editing `skills/` or `rules/`, and commit and push it before starting the next.

## Unresolved Questions
- `不明`: the real token cost of one invocation (the estimate divides bytes by four); a tokenizer count would confirm the 30 percent target.
- `不明`: how often each edge-case section is exercised in real runs (the estimate that they are rare comes from reading the workflows, not from a transcript count); Stage 5's split boundaries should be checked against recent run transcripts before it starts.
- `不明`: whether the maintainer wants Stages 6 and 7 at all if Stages 1 to 5 reach the target; they are the riskiest per byte saved.
- `不明`: whether `rules/ai-execution.md` should be split into several files or only indexed (Stage 7 assumes an index).

## AI Implementation Instruction
Implement one stage per plan, in the order above, and stop after each stage for a pipeline check before starting the next. Move text, do not reword it; keep every `MUST` and `MUST NOT`. Do not rename files that other documents cite. Add the size-budget check first, record before and after numbers for every stage, and keep all reference and structure checkers green at each commit. Do not change the meaning of any rule, and do not start a stage while another session edits the same files.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261123-155457
- **Related target files**: `skills/issue-creator/`, `skills/issue-to-plan/`, `skills/plan-to-implementation-procedure/`, `skills/code-implementation/`, `skills/git-commit-and-sync/`, `skills/DESIGN.md`, `rules/ai-execution.md`, `rules/workflow-lifecycle.md`, `rules/tool-gates.md`, `routing.md`, `prompts/01_issue-to-plan.md`, `prompts/02_plan-to-implementation-procedure.md`, `prompts/03_implementation.md`, `tools/TOOL_DESCRIPTIONS.md`, `tools/_validation_gate_defs.py`
