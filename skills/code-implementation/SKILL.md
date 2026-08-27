---
name: code-implementation
description: |
  Use this skill PROACTIVELY when converting an approved file-level implementation
  procedure document (`implementations/*.md`) into actual code changes, tests, and
  documentation updates. Covers: implementing the procedure, running lint/type/
  security validation, running targeted and full test suites, updating `docs/*.md`
  only where `docs/00_index.md`'s task-scope mapping applies, and moving the
  processed procedure document to `implementations/done/` once validated.
  Use when the task is to execute an already-written implementation procedure into
  the actual codebase — not to design, plan, or write the procedure itself.
---

# Code Implementation Skill

## Purpose

Turn an approved file-level implementation procedure document into real code changes,
tests, and (where the routing table calls for it) documentation updates. This is the
final phase of the issue → plan → implementation-procedure → code pipeline. Unlike the
two upstream phases, this phase legitimately modifies source code and `docs/*.md` — it
is not document-only.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 0 | Load required instructions | Read routing, rules, templates, and the skills needed for implementation/lint/test before starting. |
| 1 | Identify the target implementation procedure file(s) | Confirm every specified `implementations/{filename}.md` path exists before starting any processing. |
| 2 | Read the current implementation procedure file | Read it in full; extract its own Traceability values for reuse in the Final Report. |
| 3 | Implement the feature | Apply `python-implementation` + `python-lint-typecheck` guidance; fix all validation errors. |
| 4 | Test the feature | Determine targeted test scope, run it, then run the full suite exactly once. |
| 5 | Update documentation | Update only `docs/*.md` sections matched by `docs/00_index.md`'s Document References by Task table. |
| 6 | Validate documentation | Check the sections edited in Step 5, or skip if none were edited. |
| 7 | Move the completed implementation procedure file | `git mv` only, once Steps 3/4/6 pass; no human approval required. |

See `workflow.md` for the detailed per-step procedure and multi-file processing rules.

---

## Core Execution Rules

- **Code and docs are in scope**: unlike `issue-to-plan` and
  `plan-to-implementation-procedure`, this phase legitimately modifies source code and
  `docs/*.md` — see `workflow.md` Allowed file operations for the exact boundary.
- **No approval gate on the archival move**: this skill's move to
  `implementations/done/` does not require human approval — it is gated on validation
  results (Steps 3, 4, 6 passing) instead. `rules/workflow-lifecycle.md` is scoped to
  `issue-to-plan`/`plan-to-impl-procedure` only and does not apply to this workflow at
  all.
- **Documentation is routed, not guessed**: only update a `docs/*.md` section that
  `docs/00_index.md`'s "Document References by Task" table maps a changed file to — a
  changed file with no matching row is a normal, non-blocking outcome, not a defect to
  paper over.
- **One test suite run**: run the repository-defined full test suite exactly once per
  cycle, after targeted tests pass — see `workflow.md` Step 4.
- **One procedure file at a time**: see `workflow.md` Multi-file processing.
- **Move is required**: see `workflow.md` Step 7. The move MUST NOT be skipped.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

---

## Output format

This phase does not produce a single generated document — its output is code changes,
test changes, and (conditionally) `docs/*.md` edits. See `workflow.md` Final Report
for the exact chat-reporting structure (one-line traceability summary, Execution
Status, Blocker Log, Work Items Created).

---

## See Also
See `workflow.md` for detailed phase content, commands, and the toolchain reference.
See `templates/implementation-procedure.md` for the input document's structure.

---

## Composes with
- `python-implementation` — Step 3's implementation guidance
- `python-lint-typecheck` — Step 3's validation guidance
- `python-test-and-fix` — Step 4's testing guidance
- `python-debug-root-cause` — Step 4, only when a failure's cause is not immediately obvious
- `python-documentation` — Step 5, only when at least one changed file has a matching `docs/00_index.md` task-scope row

## Called by
- `plan-to-implementation-procedure` — as the next pipeline phase, once implementation procedure documents exist under `implementations/`

---

## Improvement feedback

After running this skill, if a Step needed clarification, or a documentation-mapping
edge case was missed, update `workflow.md` accordingly. If the Final Report structure
was missing a field the user consistently requested, add it to `workflow.md` Final
Report (not here).

---

## Final Rule

You are not writing a design document or a plan.

You are executing an already-approved implementation procedure into real code, tests,
and (where mapped) documentation — one procedure document per cycle, validated before
it is archived.

When in doubt, this SHOULD be prioritized: correctness over speed, minimal scope (no
unrelated refactoring), complete validation before the archival move, and
traceability back to the Plan and Issue.
