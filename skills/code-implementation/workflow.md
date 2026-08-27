# Code Implementation — Detailed Workflow

## Workflow position

```text
issue file (issues/)
  -> work plan document (plans/)
  -> file-level implementation procedure document (implementations/)
  -> implementation, tests, and documentation updates   <- this skill
```

- Input: `implementations/{filename}.md`
- Output: code changes, tests, and `docs/*.md` updates; the input file moved to `implementations/done/`
- Archive destination: `implementations/done/`
- Workflow phase: `code-implementation`

Unlike the two upstream phases, this is not a document-only phase — see Allowed file
operations below.

## Allowed file operations

- Modify source code files within the scope specified in the current implementation
  procedure document's Target file / Scope.
- Modify `docs/*.md` only for changed files with a matching `docs/00_index.md`
  "Document References by Task" row (Step 5).
- Move the processed implementation procedure file to `implementations/done/` after
  validation passes (Step 7).
- Correct the implementation procedure file itself (`implementations/{filename}.md`,
  via Edit) when Step 3's adversarial verification finds an unconfirmed item or an
  inconsistency, in addition to its `## Execution Status` section.
- Do not modify files outside the scope specified in the plan/procedure.
- Do not edit documentation before Step 5.

(`__pycache__/` is already covered by Out of Scope below's `rules/ai-execution.md`
Global Safety Restrictions (Base) — not repeated here.)

## Out of Scope

Apply `rules/ai-execution.md` Global Safety Restrictions (Base). Additionally for this
workflow, do not perform any of the following:
- moving existing documentation files
- changing workflow directory structure
- making code/behavior changes while performing Steps 5-6 (documentation update/validation)

## Multi-file processing

Apply `rules/ai-execution.md` Sequential Target Processing (Base): each cycle covers
Steps 1-7, ending with the move to `implementations/done/` in Step 7 (after the Step 5
documentation update and Step 6 validation) before starting Step 1 for the next file.

Apply `rules/ai-execution.md` Progress Reporting (Base) for the per-step report
cadence.

### Progress recording during Steps 3-6

Record your work status when a sub-task's outcome differs from what was expected, or
when moving between artifact types (code → test → doc):
- Note which artifact you are working on (code, test, or documentation)
- Record the current status (In Progress / Blocked / Completed) for each sub-task
- If blocked, describe the blocker and whether it requires user intervention
- Update the implementation procedure file's own `## Execution Status` section (via
  Edit) to reflect the current step's Status/Started/Completed — this is the
  persisted record if the session is interrupted before Step 7's move. Also update the
  Execution Status table in the final report.

---

## Step 0: Load Required Instructions

If not already loaded, read the following before starting:
- `routing.md`
- `rules/coding.md`
- `rules/toolchain.md`
- `skills/python-implementation/SKILL.md`
- `skills/python-lint-typecheck/SKILL.md`
- `skills/python-test-and-fix/SKILL.md`
- `rules/ai-execution.md`
- `templates/implementation-procedure.md`
- `templates/execution-status.md`
- `SKILL.md` (this skill), and this file.

Do not load these two eagerly — load each only at the step that actually needs it:
- `skills/python-debug-root-cause/SKILL.md` — load at Step 4, only if a failure's
  cause is not immediately obvious.
- `skills/python-documentation/SKILL.md` — load at Step 5, only if at least one
  changed file has a matching `docs/00_index.md` task-scope row.

Apply `rules/ai-execution.md` Context Reading for reuse-vs-reload of previously
loaded shared files across cycles in this session.

If a required file is missing, unreadable, or contradictory, apply
`rules/ai-execution.md` Instruction Precedence; if unresolvable, stop and report
`Blocked`. Do not infer missing instructions.

---

## Step 1: Identify the Target Implementation Procedure File(s)

- The target implementation procedure file(s) are provided by the user (e.g.
  `implementations/{filename}.md`), one path per file.
- If no target file is specified, stop immediately and ask the user to specify one or
  more.
- If any specified file does not exist, stop immediately and report which file(s) are
  missing.
- Do not read files under `implementations/done/`.

---

## Step 2: Read the Current Implementation Procedure File

- Read the current implementation procedure file in full. It follows
  `templates/implementation-procedure.md`'s structure.
- Identify the target feature and all source files to modify.
- Extract this document's own Traceability section — `Source issue`, `Source plan`,
  and `Related target files` — for reuse in this cycle's Final Report. Carry these
  values forward as-is; do not re-derive or re-guess them.
- If the implementation procedure is ambiguous or the scope is unclear, stop and ask
  for clarification before proceeding.

---

## Step 3: Implement the Feature

Before implementing, perform **adversarial verification** of the implementation
procedure's claims about current source: do not assume its Procedure/Method/Details
are still accurate — actively check via `rg`/Read whether the target file, symbol,
line numbers, and call path it describes still match current source, and whether any
assumption or scope boundary it states has since become stale or inconsistent with a
sibling procedure document or the source Plan.

If this verification finds an unconfirmed item or an inconsistency, correct the
implementation procedure document itself (`implementations/{filename}.md`, via Edit)
to reflect the corrected understanding before proceeding, and note the correction in
the Execution Status table's Notes. Do not silently implement around a stale
description — implement against the corrected, current-source-verified understanding.

Implement the feature according to the (possibly corrected) implementation procedure.
Apply the guidance loaded in Step 0 from `skills/python-implementation/SKILL.md` and
`skills/python-lint-typecheck/SKILL.md`.

After implementing:
- Run repository-defined non-test validation: formatting, linting, type checking,
  architecture/import-boundary checks, security checks.
- Fix all errors before proceeding to Step 4.

---

## Step 4: Test the Feature

Apply the guidance from `skills/python-test-and-fix/SKILL.md` (loaded in Step 0). If a
failure's cause is not immediately obvious, load
`skills/python-debug-root-cause/SKILL.md` now and apply it.

- Determine the targeted test scope via `pytest --testmon tests/` (impact-based
  selection, see `skills/python-test-and-fix/workflow.md` Step 10) when available;
  otherwise fall back to tests under the same module path as each changed file, plus
  any test found via `rg` to import a changed symbol.
- Run targeted tests during implementation.
- Fix all related failures.
- Run the repository-defined full test suite exactly once, after targeted tests
  pass — this is the only full-suite run for this cycle; Step 6 MUST NOT run tests
  again.
- Check the repository-defined coverage threshold if one exists.
- Continue to documentation only after required tests pass.

---

## Step 5: Update Documentation

Update `docs/*.md` only for changed files that fall under a Task scope row in
`docs/00_index.md`'s "Document References by Task" table (see `routing.md` Docs → task
mapping for the pointer) — do not update documentation for a changed file that falls
under no such row. If at least one changed file has a matching row, load
`skills/python-documentation/SKILL.md` now (per Step 0) and apply its guidance.

Determine which sections to update by matching each changed file against a Task scope
row's file/module list in `docs/00_index.md`'s "Document References by Task" table,
and editing only the matched row's Reference docs.

If a changed file matches no row, this is a normal, non-blocking outcome — do not
guess which doc to edit, and do not record it as a blocker. Record it in the Execution
Status table's Notes for Step 5 (e.g. `N/A: no docs/00_index.md task-scope mapping for
{file}`) so it is visible in the persisted output, not only in the transient progress
report.

If no changed file has a matching row, skip Step 6's content checks entirely (see
Step 6) and mark Step 5 Completed with the same Notes.

Move the implementation procedure file only after:
- required code validation passes,
- required tests pass,
- documentation is updated for every changed file with a matching Task scope row,
- documentation validation passes (or was skipped per Step 6, when no row matched),
- every changed file without a matching row is recorded in the Execution Status Notes.

---

## Step 6: Validate Documentation

If Step 5 made no edits (no changed file matched a Task scope row), skip this step's
content checks entirely and mark Step 6 Completed with Notes = `N/A: no documentation
changes to validate`.

Otherwise, check the sections edited in Step 5:
- Markdown structure is not broken.
- Edited relative links are valid where practical.
- Edited docs match the matched Task scope row in `docs/00_index.md`.
- No unrelated documentation files were rewritten.
- Code fences remain balanced.
- Front matter is preserved if present.

If validation surfaces an issue, fix it before proceeding to Step 7.

---

## Step 7: Move the Completed Implementation Procedure File

This step MUST NOT be skipped.

This workflow's move to `implementations/done/` does not require human approval —
proceed once Steps 3, 4, and 6 pass, without stopping to ask the user for approval.
`rules/workflow-lifecycle.md` is scoped to `issue-to-plan`/`plan-to-impl-procedure`
only and does not apply to this workflow at all.

- Do not perform this step before Step 5 (documentation update) and Step 6
  (documentation validation) are complete.
- Before proceeding, verify that:
  - the implementation procedure file's own `## Execution Status` section shows
    Completed for every step its template requires,
  - the Execution Status section in the final report accurately reflects the actual
    work performed (all completed items show Completed status, any blocked items have
    blocker descriptions filled in, Work Items Created includes all artifacts
    produced).
- Move the implementation procedure file to `implementations/done/` using `git mv`
  only. Do not use `mv`, `cp` + `rm`, or any other fallback.
- Verify the file exists in `implementations/done/` after the move.
- **If `git mv` fails, stop and report `Blocked: git mv failed — {reason}`. Do not
  fall back to another method.**

---

## Rollback on Failure

If implementation breaks existing functionality, revert changes immediately and
report `Blocked: {description}`. Do not proceed until the issue is resolved.

---

## Final Report

Include the following in the final report:

### One-line traceability summary
`Source: {impl_proc_file} | Issue: {source_issue} | Plan: {source_plan} | Target: {related_target_files} | Changed: {files} | Completed: {timestamp from date +%Y%m%d-%H%M%S}`

`{source_issue}`, `{source_plan}`, and `{related_target_files}` are the values
extracted from the implementation procedure's own Traceability section in Step 2 —
carried forward, not re-derived.

This phase edits existing code and `docs/*.md` files rather than producing a
standalone generated document, so do not insert a `## Traceability` section into
those files — the one-line summary above is this cycle's traceability record.

### Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`. Default rows for this workflow's Steps 1-7 (update
the Status column as each step starts and finishes). Leave Notes empty for a step
that completed as expected — only fill it in for a deviation (e.g. a skipped step, a
no-mapping outcome, a blocker reference):

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify the target implementation procedure file(s) | Pending | — | — | |
| 2 | Read the current implementation procedure file | Pending | — | — | |
| 3 | Implement the feature and pass code validation | Pending | — | — | |
| 4 | Test the feature and pass required tests/coverage | Pending | — | — | |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Pending | — | — | |
| 6 | Validate documentation updates | Pending | — | — | |
| 7 | Move the implementation procedure file to `implementations/done/` | Pending | — | — | |

### Blocker Log

If no blocker was encountered, report `Blockers: None` as a single line — do not
render an empty table. Otherwise, use:

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|

### Work Items Created

If no artifact beyond the planned code/test/doc changes was produced, report `Work
items created: None` as a single line — do not render an empty table. Otherwise, use:

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|

## Output format

See `SKILL.md` Output format for the reporting structure to use — this phase does not
generate a single Markdown document with a fixed structure.
