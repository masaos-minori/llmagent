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
target file listed in the plan's `Implementation Target Files` section
(`templates/plan.md`), the canonical, frozen source of implementation scope.
Document-only — see
`skills/DESIGN.md` Analysis-only phase constraint; this skill's only writes are
implementation procedure documents in `implementations/`, and moving the processed
plan file to `plans/done/`. It must not modify source code files or `docs/*.md`.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 0 | Load required instructions | Read routing, rules, templates, and this skill before starting. |
| 1 | Identify the target plan file(s) | Confirm every specified `plans/{filename}_plan.md` path exists before starting any processing. |
| 2 | Read the target plan file | Read the plan in full and extract its own `Source issue` value for reuse downstream. |
| 3 | Create implementation procedure documents | For each row in the Plan's `Implementation Target Files` table, check whether it is already implemented; if not, generate a new document per `templates/implementation-procedure.md`. |
| 4 | Move the completed plan file | `git mv` only, once Step 3 passes; no human approval required; verify pre- and post-conditions. |

See `workflow.md` for the detailed per-step procedure and multi-file processing rules.

---

## Core Execution Rules

- **One target file = one procedure document**: exactly one implementation procedure
  document per `Implementation Target Files` row; a document MUST NOT contain
  modification instructions for more than one file — see `workflow.md` Step 3.
- **No duplicate work**: a target file row may be skipped only when an existing
  document under `implementations/` or `implementations/done/` has both a matching
  `Source plan` and a matching `Related target files` (by `target_file_path`, not
  `target_file_name`) — see `workflow.md` Step 3.
- **Sortable, collision-safe naming**: output filenames are
  `{timestamp}_{seq}_{target_file_slug}.md`. `target_file_slug` is `target_file_path`
  (not `target_file_name`) with `/` and any non-alphanumeric/`_`/`-`/`.` character
  replaced by `_`. `timestamp` is captured once and shared across every document
  generated in one Step 3 pass; `seq` is the row's 1-indexed, zero-padded position
  within the plan's `Implementation Target Files` table — see `workflow.md` Step 3.
- **Frozen-inventory revalidation**: before generating any procedure document,
  revalidate the Plan's `Implementation Target Files` section per
  `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan Freeze) —
  see `workflow.md` Step 2.
- **Blocked on new target discovery**: if implementing a target file requires
  modifying a file not listed in `Implementation Target Files`, stop and report
  `Blocked` — do not generate further procedure documents until the Plan is amended
  and revalidated — see `workflow.md` Step 3.
- **One plan at a time**: see `workflow.md` Multi-file processing.
- **Move is required**: see `workflow.md` Step 4. The move MUST NOT be skipped.
- **No approval gate on the archival move**: this skill's move to `plans/done/`
  does not require human approval — it is gated on Step 3's validation and Step 4's
  pre-move checklist passing instead, per `rules/workflow-lifecycle.md` Validation
  Reporting.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.
- Exception to `skills/DESIGN.md` Output language: write the generated implementation
  procedure documents in clear and concise English (this skill's output feeds
  directly into `python-implementation` / `code-implementation` for AI consumption).

---

## Output format

Generate `implementations/{timestamp}_{seq}_{target_file_slug}.md` (naming per Core
Execution Rules above) using the exact Markdown structure defined in
`templates/implementation-procedure.md`. Do not omit any section. Sorting generated
filenames by `seq` reproduces the plan's implementation order — see `workflow.md`
Step 3.

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
- `python-implementation` — executes the generated implementation procedure documents

## Called by
- `issue-to-plan` — as the next pipeline phase once a Plan is approved

---

## Improvement feedback

If a generated document's field is consistently missing or unclear, update
`templates/implementation-procedure.md` directly (not this file) — it is the
canonical, shared output-format definition. If a Step needs clarification or a
duplicate-work check produces a false positive/negative, update `workflow.md`.

---

## Final Rule

You are not writing an architecture document — you are converting an approved Plan
into small, file-level, independently reviewable implementation and test procedures,
one per target file, ready for `python-implementation` to execute.

When in doubt, this SHOULD be prioritized: no duplicate work, collision-safe naming,
traceability back to the Plan and Issue, and minimal but complete per-file procedures.
