---
name: plan-to-implementation-procedure
description: |
  Use this skill PROACTIVELY when converting an approved work plan (`plans/*.md`)
  into file-level implementation procedure documents (`implementations/*.md`), one
  per row of the Plan's frozen `Implementation Target Files` table. Covers: matching
  target file rows against existing implementation procedures to avoid duplicate
  work, applying narrow `python-design` guidance to a few fields, generating a
  sortable, collision-safe output filename, and moving the processed plan to
  `plans/done/` once validated.
  Use when breaking an approved plan into concrete, file-level implementation and
  test procedures — not to design architecture, and not to implement anything.
---

# Plan To Implementation Procedure Skill

## Purpose

Turn an approved work plan into file-level implementation procedure documents, one per
target file in the plan's `Implementation Target Files` section (`templates/plan.md`),
the canonical, frozen source of implementation scope.
Document-only — see `skills/DESIGN.md` Analysis-only phase constraint. The only writes
are implementation procedure documents in `implementations/` and the move of the
processed plan file to `plans/done/`. This skill MUST NOT modify source code files or
`docs/*.md`.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 0 | Load required instructions | Read routing, rules, templates, and this skill before starting. |
| 1 | Identify the target plan file(s) | Confirm every specified `plans/{filename}.md` path exists before starting any processing. |
| 2 | Read the target plan file | Check the Plan's structure, confirm `Freeze status` is `Frozen`, check the Plan-level start conditions (no `Blocking? = True` Unknown, no open Dependency, Frozen-Plan overlaps judged), revalidate the frozen inventory, then read the plan in full and extract its own `Source issue` value for reuse downstream. |
| 3 | Create implementation procedure documents | For each row in the Plan's `Implementation Target Files` table, check whether it is already implemented; if not, generate a new document per `templates/implementation-procedure.md`. |
| 4 | Move the completed plan file | Update the Plan's Execution Status (mapped steps only) and `Work Items Created`, then `git mv` only, once Step 3 passes; no human approval required; verify pre- and post-conditions; emit the final report. |

See `workflow.md` for the detailed per-step procedure and multi-file processing rules.

---

## Core Execution Rules

- **One target file = one procedure document**: each cycle generates at most one
  document per `Implementation Target Files` row; a document MUST NOT contain
  modification instructions for more than one file. For a `Partially implemented` row,
  the existing document that already covers part of the row and the one remainder
  document this cycle generates together cover the row (`workflow.md` Step 3c).
- **No duplicate work**: a row may be skipped only when an existing document under
  `implementations/` or `implementations/done/` has both a matching `Source plan` and a
  matching `Related target files` (by `target_file_path`, not `target_file_name`).
- **Sortable, collision-safe naming**: see `workflow.md`, section "Workflow position",
  for the `{timestamp}_{seq}_{target_file_slug}.md` naming algorithm.
- **Frozen-inventory revalidation**: before generating any document, revalidate the
  Plan's `Implementation Target Files` section per `rules/workflow-lifecycle.md`
  Implementation Target Files Validation (Plan Freeze) — see `workflow.md` Step 2.
- **Blocked on new target discovery**: if implementing a target file requires
  modifying a file not listed in `Implementation Target Files`, stop and report
  `Blocked` — MUST NOT generate further documents until the Plan is amended and
  revalidated.
- **One plan at a time**: see `workflow.md` Multi-file processing.
- **Move is required** (`workflow.md` Step 4): it MUST NOT be skipped once its
  gate holds — every row is covered by a document — and MUST NOT happen while any row
  ended `Blocked`, `Plan Gap`, or `Needs confirmation` without a document. It needs no
  human approval; it is gated on Step 3's validation and Step 4's pre-move checklist
  (`rules/workflow-lifecycle.md` Validation Reporting).
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.
- Output language: see `skills/DESIGN.md` §Output language.

---

## Output format

Generate `implementations/{timestamp}_{seq}_{target_file_slug}.md` (naming per Core
Execution Rules above) using the exact Markdown structure defined in
`templates/implementation-procedure.md`. MUST NOT omit any section. Sorting filenames by
`seq` reproduces the plan's implementation order — see `workflow.md` Step 3.

---

## See Also
See `workflow.md` for detailed phase content.
See `templates/plan.md` for the input Plan's structure.
See `templates/implementation-procedure.md` for the output structure.

---

## Composes with
- `python-design` — for the "Design decisions" / "Alternatives considered" /
  "Compatibility considerations" / "Security considerations" / "Rollback
  considerations" fields (a few relevant bullets only, not a full invocation)
- `code-implementation` — executes the generated implementation procedure documents,
  applying `python-implementation`'s guidance

## Called by
- `issue-to-plan` — as the next pipeline phase once a Plan is approved

---

## Improvement feedback

A consistently missing or unclear document field: update
`templates/implementation-procedure.md` (the canonical output format), not this file. A Step needing clarification or a
false positive/negative duplicate-work check: update `workflow.md`.

---

## Final Rule

You are not writing an architecture document — you are converting an approved Plan
into small, file-level, independently reviewable implementation and test procedures,
one per target file, ready for `code-implementation` to execute.

When in doubt, this SHOULD be prioritized: no duplicate work, collision-safe naming,
traceability back to the Plan and Issue, and the scope discipline of `AGENTS.md`
Global Rule 5.
