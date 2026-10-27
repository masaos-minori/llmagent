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
tests, and (where the routing table calls for it) documentation updates. Final phase
of the issue → plan → implementation-procedure → code pipeline. Unlike the two
upstream phases, this phase legitimately modifies source code and `docs/*.md`.

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 0 | Load required instructions | Read routing, rules, templates, and the implementation/lint/test skills before starting. |
| 1 | Identify the target implementation procedure file(s) | Confirm every specified `implementations/{filename}.md` path exists before processing. |
| 2 | Read the current implementation procedure file | Read in full; extract its Traceability values for reuse in the Final Report. Then run pre-execution stale detection: verify the procedure's referenced code constructs still exist in current source; abort if stale. |
| 3 | Implement the feature | Apply `python-implementation` + `python-lint-typecheck` guidance; fix all validation errors. |
| 4 | Test the feature | Determine targeted test scope, run it, then run the full suite once (retry on failure within Attempt Limit). |
| 5 | Update documentation | Update only `docs/*.md` sections matched by `docs/00_index.md`'s Document References by Task table. |
| 6 | Validate documentation | Check the sections edited in Step 5, or skip if none were edited. |
| 7 | Move the completed implementation procedure file | `git mv` only, once Step 2 (stale detection) and Steps 3/4/5/6 pass; no human approval required. |

See `workflow.md` for the detailed per-step procedure and multi-file processing
rules, and `templates/implementation-procedure.md` for the input document's
structure.

## Core Execution Rules

- Code and docs are in scope, unlike `issue-to-plan` and
  `plan-to-implementation-procedure`. See `workflow.md` Allowed file operations for
  the exact boundary.
- The move to `implementations/done/` needs no human approval; it is gated on Step 2 (stale detection) and Steps 3/4/5/6 passing. `rules/workflow-lifecycle.md` applies here only through Target Validation and Correction-and-Recheck Cycle Bound, not its Archival Move or Plan Freeze rules (`workflow.md` Step 7).
- Documentation is routed, not guessed: only update a `docs/*.md` section that
  `docs/00_index.md`'s "Document References by Task" table maps a changed file to. A
  changed file with no matching row is a normal, non-blocking outcome.
- Run the repository-defined full test suite once per cycle after targeted tests
  pass; a failure may be fixed and re-run within Attempt Limit (3 attempts) (`workflow.md` Step 4).
- Process one procedure file at a time. See `workflow.md` Multi-file processing. A
  `Blocked` cycle stops the remaining procedures of the same Plan until the user decides
  (Dependency order).
- The procedure's own Execution Status has the template's four rows, mapped to Steps in
  `workflow.md` Progress recording (Row mapping). Do not use `close-batch`: it marks every
  row `Completed` regardless of actual state (`workflow.md` Step 7).
- The procedure's `Validation plan`, `Completion criteria`, `Rollback considerations`, and
  `Out of Scope` sections are binding inputs to Steps 3-7, not background.
- The move MUST NOT be skipped. See `workflow.md` Step 7.
- Pre-execution stale detection (`workflow.md` Step 2): abort if any referenced construct is missing from current source; any single mismatch is "stale"; report all failures in a single pass.
- Archive destination already exists (`workflow.md` Step 7): source gone means already archived; both exist means `Blocked` — never rename to a disambiguated path.
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

## Output format

Output is code changes, test changes, and (conditionally) `docs/*.md` edits, not a
single generated document. See `workflow.md` Final Report for the chat-reporting
structure (one-line traceability summary, Execution Status, Blocker Log, Work Items
Created).

## Composes with
- `python-implementation` — Step 3's implementation guidance
- `python-lint-typecheck` — Step 3's validation guidance
- `python-test-and-fix` — Step 4's testing guidance
- `python-debug-root-cause` — Step 4, only when a failure's cause is not immediately obvious
- `python-documentation` — Step 5, only when at least one changed file has a matching `docs/00_index.md` task-scope row
- `git-commit-and-sync` — run after the cycle(s) to commit the changes together with the staged archival rename; this skill never commits the code itself
- `deploy` — only on the user's request, after the change is pushed, when `scripts/` files were added, removed, or renamed

## Called by
- `plan-to-implementation-procedure` — as the next pipeline phase, once implementation procedure documents exist under `implementations/`

## Improvement feedback

After running, if a Step needed clarification or a documentation-mapping edge case was
missed, update `workflow.md` (a missing Final Report field goes in `workflow.md` Final Report, not here).

## Final Rule

You are executing an already-approved implementation procedure into real code, tests,
and (where mapped) documentation, one procedure document per cycle, validated before
it is archived.

When in doubt, this SHOULD be prioritized: correctness over speed, minimal scope (see
`AGENTS.md` Global Rule 5), complete validation before the archival move, and
traceability back to the Plan and Issue.
