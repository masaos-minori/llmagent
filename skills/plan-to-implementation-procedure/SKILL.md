---
name: plan-to-implementation-procedure
description: |
  Use this skill PROACTIVELY when converting an approved work plan (`plans/*.md`)
  into file-level implementation procedure documents (`implementations/*.md`), one
  document per target file. Covers: matching plan items against already-generated
  implementation procedures to avoid duplicate work, applying narrow design-reasoning
  guidance from `python-design` to a small set of fields, generating a sortable,
  collision-safe output filename, and moving the processed plan to `plans/done/`
  after approval.
  Use when the task is to break an approved plan into concrete, file-level
  implementation and test procedures — not to design architecture, and not to
  implement anything.
---

# Plan To Implementation Procedure Skill

## Purpose

Turn an approved work plan into file-level implementation procedure documents, one per
target file identified in the plan's `Implementation steps`. Document-only — see
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
| 3 | Create implementation procedure documents | For each `Implementation steps` item, check whether it is already implemented; if not, generate a new document per `templates/implementation-procedure.md`. |
| 4 | Move the completed plan file | `git mv` only, after explicit approval; verify pre- and post-conditions. |

See `workflow.md` for the detailed per-step procedure and multi-file processing rules.


---

## Core Execution Rules (Strictly Enforced)

- **No duplicate work**: an `Implementation steps` item may be skipped only when an
  existing document under `implementations/` or `implementations/done/` has both a
  matching `Source plan` and a matching `Related target files` (by `target_file_path`,
  not `target_file_name`) — see `workflow.md` Step 3.
- **Sortable, collision-safe naming**: output filenames are
  `{timestamp}_{seq}_{target_file_slug}.md`. `target_file_slug` is `target_file_path`
  (not `target_file_name`) with `/` replaced by `_`, and any character that is not
  alphanumeric, `_`, `-`, or `.` also replaced by `_` — so two target files with the
  same base name in different directories never collide, and the result stays a valid
  filename across filesystems and shells. `timestamp` is captured once and
  shared across every document generated in one Step 3 pass; `seq` is the item's
  1-indexed, zero-padded position within the plan's `Implementation steps` list.
  Sorting the generated filenames lexicographically therefore reproduces the plan's
  implementation order — see `workflow.md` Step 3.
- **One plan at a time**: see `workflow.md` Multi-file processing.
- **Mandatory move**: see `workflow.md` Step 4. Do not skip it.
- **No approval-gate confusion**: this skill's move to `plans/done/` DOES require
  explicit user approval — Approval Handling in `rules/workflow-lifecycle.md` is
  scoped to document-generation workflows, which this is (unlike the subsequent
  code-implementation phase, whose move is gated by validation results instead).
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

---

## Output format

Generate `implementations/{timestamp}_{seq}_{target_file_slug}.md` using the exact
Markdown structure defined in `templates/implementation-procedure.md`. Do not omit any
section. `seq` is the item's 1-indexed, zero-padded position within the plan's
`Implementation steps` list, so sorting filenames reproduces the implementation order
— see `workflow.md` Step 3.

---

## See Also
See `workflow.md` for detailed phase content.
See `templates/plan.md` for the input Plan's structure.
See `templates/implementation-procedure.md` for the output structure.

---

## Composes with
- `python-design` — for how to reason about the "Design decisions" / "Alternatives
  considered" / "Compatibility considerations" / "Security considerations" /
  "Rollback considerations" fields; only a few relevant bullets are drawn from its
  broader template, not a full invocation of that skill
- `python-implementation` — executes the generated implementation procedure documents

## Called by
- `issue-to-plan` — as the next pipeline phase once a Plan is approved

---

## Improvement feedback

After running this skill, if a generated document's field was consistently missing or
unclear, update `templates/implementation-procedure.md` directly (not this file — it
is the canonical output-format definition, shared with every consumer of this
workflow phase). If a Step needed clarification or a duplicate-work check produced a
false positive/negative, update `workflow.md` accordingly.

---

## Final Rule

You are not writing an architecture document.

You are converting an approved Plan into small, file-level, independently reviewable
implementation and test procedures — one per target file, ready for
`python-implementation` to execute.

When in doubt, prioritize: no duplicate work, collision-safe naming, traceability back
to the Plan and Issue, and minimal but complete per-file procedures.
