---
name: issue-to-plan
description: |
  Use this skill PROACTIVELY when converting a raw, unformatted issue
  (`issues/*.md`) directly into a concrete Python implementation plan
  (`plans/*.md`), with no standalone requirement document in between.
  Covers: verifying the issue's claims against current source, deciding
  whether the issue is already resolved or too vague to act on, task-size
  classification (Path A/B), architecture/dependency/historical analysis,
  operational dependency inspection, validation quality analysis, and
  uncertainty tracking.
  Use when the task needs scope definition, affected files, implementation
  steps, test strategy, risks, assumptions, unknowns, or execution
  sequencing before coding — starting directly from a raw issue.
---

# Issue To Plan Skill

## Purpose

Turn a raw issue directly into a concrete, reviewable implementation plan: verify the
issue's claims against current source, then ground the plan in architecture analysis and
historical data. No standalone requirement document is produced; evidence verification
and planning happen in one continuous cycle. Document-only — see `skills/DESIGN.md`
Analysis-only phase constraint; this skill's only writes are the plan document in
`plans/`, optional `issues/{timestamp}_unknowns.md` / `issues/{timestamp}_risks.md`
files, and moving the processed issue file to `issues/done/`. It MUST NOT modify source
code files or `docs/*.md`.

Issue filenames follow `{timestamp}_{id}_{slug}.md` (defined in `skills/issue-creator`
Issue Filename Generation), enabling automatic duplicate detection via Step 2.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 0 | Load required instructions | Read routing, rules, templates, and this skill before starting. |
| 1 | Identify target Issues | Confirm every specified `issues/{filename}.md` path exists before any processing. Then check for an existing Plan (`workflow.md` Step 1b): a Plan that is not `Frozen` never allows the Issue to be moved. |
| 2 | Assess the current Issue | Read the Issue in full, verify its claims against current source, and classify each extracted item's evidence basis. If already resolved or no longer applicable, stop and report; MUST NOT write a Plan. |
| 3 | Inspect related files | Classify the Issue as Path A or B (see Routing below), then inspect related source, tests, config, and docs at the depth the Path calls for. |
| 4 | Map Issue information to Plan information | Build an explicit mapping from every extracted Issue item to its Plan destination before writing anything. |
| 5 | Create the Plan | Apply Path B's broader analysis if applicable, then generate `plans/{timestamp}_plan.md` with stable Requirement IDs. |
| 6 | Analyze Unknowns and Risks | Resolve what evidence allows; file unresolved blocking items as issues. |
| 7 | Add Traceability | Fill the canonical Traceability fields and the per-Requirement Requirement Traceability table. |
| 8 | Validate information completeness | Confirm no Issue information was dropped, every Requirement ID is traceable, and `Implementation Target Files` passes validation and is marked `Frozen`. `Fail`/`Partial` or a not-`Frozen` section re-enters Step 8 (see `workflow.md` Step 8c); the Issue is not moved. |
| 9 | Final validation | Confirm all Step 8 checks pass (including `Frozen`); report the outcome. On `Fail`/`Partial`/`Blocked`, stop here; MUST NOT proceed to Step 10. |
| 10 | Move the Issue | `git mv` only, once Step 9 passes and the Plan is `Frozen` (never for a `Draft` Plan or a `Blocked` cycle); no human approval required; no fallback. |

See `workflow.md` for the per-step procedure and multi-file processing rules.
See `workflow-path-b.md` for the Path B-only toolchain and analysis (load it at Step 5, only when
Step 3 determined Path B).

---

## Routing (AI Task Size Assessment)

Before any analysis step, execute **Step 3's classification** (this skill's task-size
assessment, carried forward unchanged from its predecessor). Assess the current Issue
against the following criteria to determine the execution path.

### [Path A] Small Task
**Criteria (MUST satisfy ALL):**
- [ ] Affects ≤ 3 files
- [ ] No public or runtime-facing interface changes
- [ ] No database schema changes

**Execution Path:**
Perform Step 3's direct-verification inspection only (no architecture/dependency/
historical/operational analysis) → establish the validation quality baseline in
Step 5 → Steps 6-10 run unconditionally.

### [Path B] Large Task
**Criteria (Satisfies ANY):**
- [ ] Affects > 3 files
- [ ] Creates a new module or package
- [ ] Changes a public/runtime interface
- [ ] Modifies or adds a database schema

**Execution Path:**
Load `workflow-path-b.md` at Step 5 (not eagerly in Step 0 — only once Step 3 determines
Path B) and perform its full analysis (architecture, dependency graphing, historical
analysis, operational dependency inspection), then `workflow.md` Step 5's validation
quality analysis. MUST NOT skip any analysis.

> Tool Availability Guard: applies to `pydeps`, `radon`, `semgrep`, and any other tool
> used in `workflow.md` / `workflow-path-b.md` — see `skills/DESIGN.md` Tool availability
> guard.

---

## Core Execution Rules

- **No Guesswork**: Verify the Issue's factual claims (affected files, whether the
  described problem still reproduces) against current source before writing anything.
  Every file listed in `Implementation Target Files` or `Reference Files` MUST be
  verified via environment tools per `rules/workflow-lifecycle.md` Implementation Target
  Files Validation (Plan Freeze); MUST NOT guess filenames or directory structures.
- **Isolate Unknowns**: If you lack context or code access to answer a question, mark it
  as `BLOCKING: True` in Step 6 and ask the user for clarification before generating the
  final implementation steps.
- **Incrementalism**: Design implementation steps in small, reviewable increments; reuse
  this skill's Path A ≤3-file threshold (see Routing above) as the size bound per step,
  where applicable. Each step MUST leave the codebase in a testable state.
- **One Issue at a time**: see `workflow.md` Multi-file processing.
- **Frozen scope**: the Plan's `Implementation Target Files` section is the canonical,
  frozen source of implementation scope once Step 8 validates it — see
  `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze).
- **No approval gate on the archival move**: the move to `issues/done/` requires no
  human approval; it is gated on Step 9's validation passing, per
  `rules/workflow-lifecycle.md` Validation Reporting.
- **Move is required**: see `workflow.md` Step 10. The move MUST NOT be skipped once its gate passes, and MUST NOT happen while the Plan is `Draft`/not `Frozen` or the cycle is `Blocked`.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.
- Output language: see `skills/DESIGN.md` §Output language.

---

## Output format

Generate `plans/{timestamp}_plan.md` (e.g. `plans/20260702-120000_plan.md`) using the
exact Markdown structure defined in `templates/plan.md`. MUST NOT omit any section. The
plan file is the working document: update it as scope changes. MUST NOT implement
directly from it; the next pipeline phase is `plan-to-implementation-procedure`, which
produces the procedure documents `code-implementation` executes (see Composes with).

## See Also
See `workflow.md` for detailed phase content, commands, and the toolchain reference.
See `rules/env.md` for service ports, DB schema, and module decomposition.

## Composes with
- `plan-to-implementation-procedure` — the next pipeline phase once the plan is approved; converts it into file-level implementation procedure documents
- `code-implementation` — executes the resulting implementation procedure documents, applying `python-implementation`'s guidance
- `python-refactoring` — if the plan involves structural module changes
- `mcp-server-add` — if the plan includes adding a new MCP server

## Improvement feedback

After running this skill, if a tool was not installed or a step produced no useful
evidence: update `workflow.md` with the lightweight alternative and the "if installed"
guard. If the Plan output structure was missing a field the user consistently
requested, add it to `templates/plan.md` (not here). If an Issue input field was
consistently missing or ambiguous, add it to `templates/issue.md` (shared with
`skills/issue-creator`), not to this skill's files. If a Step needed clarification,
update `workflow.md`.
