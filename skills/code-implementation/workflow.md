# Code Implementation — Detailed Workflow

## Workflow position

See `routing.md`, section 'Document workflow directories'.

- Input: `implementations/{filename}.md`
- Output: code changes, tests, and `docs/*.md` updates; the input file moved to `implementations/done/`
- Archive destination: `implementations/done/`
- Superceded archive destination: `implementations/superseded/`
- Workflow phase: `code-implementation`

Unlike the two upstream phases, this is not a document-only phase — see Allowed file
operations below.

## Toolchain

Tools this workflow's Steps use, satisfying `rules/ai-execution.md` Repository Tool
Usage #1's inspection obligation for the needs named here (a new need not covered
below still requires the full inspection that rule describes):

| Tool | Step | Role |
|---|---|---|
| `tools/manage_workitem_stage.py close-implementation` | 1, 7 | `git mv`-based archival move (see below for its refusal condition) |
| `ruff format`, `ruff check` | 3e | Formatting and lint |
| `mypy` / `pyright` | 3e | Type checking |
| `lint-imports` | 3e | Architecture/import-boundary check |
| `bandit` | 3e | Security check |
| `pytest` (targeted, then full suite), `pytest --testmon` | 4 | Test execution and impact-based selection |
| `tools/check_docs_quality.py`, `tools/check_docs_structure.py`, `tools/check_docs_consistency.py --domain <domain>` | 6 | Documentation validation |

`tools/manage_workitem_stage.py close-implementation` (see `tools/TOOL_DESCRIPTIONS.md`
for full usage) is a `git mv`-based archival move that refuses (non-zero exit, no move)
if the target's `## Execution Status` table still has a `Pending` row, without
`--force --reason`. Per `rules/ai-execution.md` Repository Tool Usage, prefer it over a
direct `git mv` when it covers the need; Step 1 and Step 7 below state the fallback to
use if the tool is unavailable.

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

For whether a resumed batch is safe to re-run without re-executing already-completed
files, see Step 1's All-steps-completed check.

Apply `rules/ai-execution.md` Progress Reporting (Base) for the per-step report
cadence.

### Progress recording during Steps 3-6

**Chat-report frequency** (when to tell the user something): "differs from expected"
means one of these concrete conditions — a Step reports `Blocked`, an Attempt Limit
retry occurred, a Rollback was applied, or a Step's outcome is `N/A`/skipped. Report
status only on one of these, or when moving between artifact types (code → test →
doc):
- Note the current artifact (code, test, or documentation)
- Record status (In Progress / Blocked / Completed) per sub-task
- If blocked, describe the blocker and whether it requires user intervention

A chat report is informational only — reporting a status never itself restarts, retries,
or re-verifies a Step; only the Step's own defined trigger conditions (Attempt Limit,
Adversarial Verification finding, etc.) do that.

**Execution Status file write** (unconditional, independent of the chat-report
frequency gate above): update the implementation procedure file's own
`## Execution Status` section (via Edit) with the current step's Status/Started/
Completed at every Step transition or completion within Steps 3-6, regardless of
whether a chat report is also made for that transition — this is the persisted
record if the session is interrupted before Step 7's move. Also update the final
report's Execution Status table. This Edit targets only the `## Execution Status`
section — it is never itself a claim about current source that Step 3a's Adversarial
Verification would need to re-check on a later cycle.

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

Apply `rules/ai-execution.md` Context Reading for reuse of previously loaded shared
files across cycles in this session.

Apply `rules/ai-execution.md`, section 'Required File Validation'.

## Step 1: Identify the Target Implementation Procedure File(s)

- The target implementation procedure file(s) are provided by the user (e.g.
  `implementations/{filename}.md`), one path per file.
- If no target file is specified, stop immediately and ask the user to specify one or
  more.
- If any specified file does not exist, stop immediately and report which file(s) are
  missing.
- Do not read files under `implementations/done/`.
- **All-steps-completed check**: after reading the file, inspect its `## Execution Status`
  table. If every step row shows `Completed` (no `Pending`, `Blocked`, or other status),
  the procedure is fully executed — do not re-execute it. Move it to
  `implementations/done/` (same rules as Step 7): prefer `uv run python
  tools/manage_workitem_stage.py close-implementation implementations/{filename}.md`;
  fall back to `git mv implementations/{filename}.md implementations/done/{filename}.md`
  only if the tool is unavailable. Verify the file exists in `implementations/done/`
  after the move. Report
  `Moved to done: {filename} — all steps Completed, no further action needed`.
  If this move fails, the same continuation policy applies: report `Blocked` for this
  file only and continue to the next target file in the batch (see Step 7).
- **Partial-completion resume**: if at least one row is `Completed` but not all
  (a resumed, previously-interrupted cycle), resume from the first Step whose row is
  not `Completed` — do not re-run a Step already marked `Completed` in this table
  unless a later Step's Adversarial Verification (Step 3a) specifically finds that
  Step's output is now stale. Do not re-derive or re-verify a `Completed` Step's
  conclusion merely because the cycle is resuming.

## Step 2: Read the Current Implementation Procedure File

- Read the current implementation procedure file in full. It follows
  `templates/implementation-procedure.md`'s structure.
- Identify the target feature and all source files to modify.
- Extract this document's own Traceability section — `Source issue`, `Source plan`,
  and `Related target files` — for reuse in this cycle's Final Report. Carry these
  values forward as-is; do not re-derive or re-guess them.
- If the implementation procedure is ambiguous or the scope is unclear, stop and ask
  for clarification before proceeding.

## Step 3: Implement the Feature

This step has five sub-steps, applied in order: verify the procedure's claims (3a),
correct the procedure on a finding (3b), check for cross-file conflicts (3c), implement
(3d), then validate (3e).

### Step 3a: Verify the procedure's claims (adversarial verification)

Before implementing, apply `rules/ai-execution.md` Adversarial Verification (Base) to
the procedure's claims about current source: do not assume its Procedure/Method/Details
are still accurate — check via `rg`/Read whether the target file, symbol, line numbers,
and call path it describes still match current source, and whether any stated
assumption or scope boundary is stale or inconsistent with a sibling procedure document
or the source Plan. Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule:
do not re-run a `rg`/Read check already performed against this same file at its current
content within this cycle.

**Completed when**: the target file, its specific symbol/line/call-path claims, and its
stated dependencies have each been checked once against current source.

### Step 3b: Correct the procedure document on a finding

If verification finds an unconfirmed item or an inconsistency, correct the
implementation procedure document itself (`implementations/{filename}.md`, via Edit)
to reflect the corrected understanding before proceeding, and note the correction in
the Execution Status table's Notes. Do not implement around a stale description —
implement against the corrected, source-verified understanding.

This file's procedure tolerates at most 3 consecutive correction-and-recheck cycles
(re-running Step 3a against the corrected document, per `AGENTS.md` Loop Prevention >
Attempt Limit — the same 3-attempt bound, applied to procedure-correction cycles
specifically). If a clean Step 3a pass (no new finding) is not reached within that
bound, stop and report `Blocked: implementation procedure requires more than 3
correction cycles — {summary of all remaining unresolved findings}` rather than
continuing to patch.

**Completed when**: no unconfirmed item or inconsistency from Step 3a remains
unaddressed in the procedure document (or Step 3a found none).

### Step 3c: Check for cross-file conflicts

If adversarial verification, or the implementation itself, reveals that the current
file's required change conflicts with, or invalidates an assumption of, an
already-processed file's change in the same Multi-file-processing batch, stop and
report `Blocked: cross-file conflict with {earlier file} — {description}` rather than
proceeding. Do not implement around the conflict silently. This is a per-file `Blocked`
outcome, not a batch-wide stop — the current file's cycle ends here, its Execution
Status row for this Step is marked `Blocked`, and Multi-file processing continues with
the next target file in the batch (same continuation policy as Step 7's move failure).

**Completed when**: no unresolved conflict with an already-processed file in this batch
is outstanding.

### Step 3d: Implement

Implement the feature per the (possibly corrected) procedure, applying the guidance
loaded in Step 0 from `skills/python-implementation/SKILL.md` and
`skills/python-lint-typecheck/SKILL.md`. Record the changed file list in this Step's
Execution Status Notes as it is produced — this is the list Final Report's `{files}`
reads back (see Final Report below), not a list recomputed from `git diff` at report
time.

**Completed when**: the change described in the (possibly corrected) procedure is
applied and its file list is recorded.

### Step 3e: Validate

Run repository-defined non-test validation: formatting, linting, type checking,
architecture/import-boundary checks, security checks.

**Completed when**: all of the above pass — for a tool with countable output (e.g.
`pytest`'s collected-item count), confirm it actually ran against a non-empty target,
not merely that its exit code was 0 (per `rules/ai-execution.md` Repository Tool Usage #8).
**On a failure**: fix the code and re-run this same Step 3e (not Step 3a-3d) until it
passes. Per AGENTS.md Attempt Limit, each distinct error/failure may be attempted at
most 3 times before stopping. Per AGENTS.md Failure Log, each failed attempt must be
recorded (approach, error, reason) before trying a different approach. If the Attempt
Limit is reached, apply Rollback on Failure below.

## Step 4: Test the Feature

Apply the guidance from `skills/python-test-and-fix/SKILL.md` (loaded in Step 0). If a
failure's cause is not immediately obvious, load and apply
`skills/python-debug-root-cause/SKILL.md` now.

- Determine the targeted test scope via `pytest --testmon tests/` (impact-based
  selection, see `skills/python-test-and-fix/workflow.md` Step 10) when available;
  otherwise use tests under the same module path as each changed file, plus any test
  found via `rg` to import a changed symbol.
- Run targeted tests during implementation; confirm the run actually collected at least
  one test (a 0-collected, exit-0 run is not a pass — per `rules/ai-execution.md`
  Repository Tool Usage #8) before treating it as evidence either way; fix all related
  failures. Per AGENTS.md Attempt Limit, each distinct error/failure may be attempted at
  most 3 times before stopping. Per AGENTS.md Failure Log, each failed attempt must be
  recorded (approach, error, reason) before trying a different approach. If the Attempt
  Limit is reached without a passing fix, stop and apply Rollback on Failure (below) —
  do not proceed to the full-suite run with a known-failing targeted test. If a fix here
  touched formatting, typing, or imports, re-run Step 3e before returning to this Step's
  targeted tests — do not treat Step 3e as satisfied by its earlier pass.
- Run the repository-defined full test suite exactly once per cycle, after targeted
  tests pass and confirmed to have collected at least one test — the only full-suite
  run for this cycle; Step 6 MUST NOT run tests again. If it fails, fixing and re-running
  the full suite is subject to the same Attempt Limit (3 attempts) and Failure Log as
  targeted tests above — this re-run is the one exception to "exactly once" for an
  ordinary failure; reaching the Attempt Limit without a passing full-suite run means
  applying Rollback on Failure (below), not a fourth attempt.
  If Step 3 reported a cross-file conflict with an already-processed earlier file (see
  Step 3), re-run the full test suite for that earlier file's implementation procedure
  cycle before continuing the batch — this is a second, independent exception to
  "exactly once," scoped strictly to the conflict-detected case.
- Check the repository-defined coverage threshold if one exists.
- Continue to documentation only after required tests pass.

## Step 5: Update Documentation

Update `docs/*.md` only for changed files under a Task scope row in
`docs/00_index.md`'s "Document References by Task" table (see `routing.md` Docs → task
mapping for the pointer) — not for a changed file under no such row. Match each
changed file against the table's file/module list and edit only the matched row's
Reference docs. If at least one changed file has a matching row, load
`skills/python-documentation/SKILL.md` now (per Step 0) and apply its guidance.

If a changed file matches no row, this is a normal, non-blocking outcome — do not
guess which doc to edit, and do not record it as a blocker. Record it in the Execution
Status table's Notes for Step 5 (e.g. `N/A: no docs/00_index.md task-scope mapping for
{file}`) so it is visible in the persisted output, not only in the transient progress
report.

If no changed file has a matching row, skip Step 6's content checks entirely (see
Step 6) and mark Step 5 Completed with the same Notes.

Move the implementation procedure file only after:
- required code validation and tests pass,
- documentation is updated for every changed file with a matching Task scope row,
- documentation validation passes (or was skipped per Step 6, when no row matched),
- every changed file without a matching row is recorded in the Execution Status Notes.

## Step 6: Validate Documentation

If Step 5 made no edits (no changed file matched a Task scope row), skip this step's
content checks entirely and mark Step 6 Completed with Notes = `N/A: no documentation
changes to validate`.

Otherwise, run the checkers `routing.md` Tools → "When to run which tool" requires
for an edited `docs/*.md` file (per `AGENTS.md` Global Rule 9 — do not rely on
manual review alone for what these already automate): `uv run python
tools/check_docs_quality.py` and `uv run python tools/check_docs_structure.py
[edited files...]` always; add `uv run python tools/check_docs_consistency.py
--domain <domain>` when the edited docs fall under a domain that checker covers
(`agent`/`mcp`/`rag`/`deployment`/`overview`).

These tools cover most of the check below; still confirm manually whatever they do
not automate for the edited sections:
- Markdown structure is not broken.
- Edited relative links are valid where practical.
- Edited docs match the matched Task scope row in `docs/00_index.md`.
- No unrelated documentation files were rewritten.
- Code fences remain balanced.
- Front matter is preserved if present.

If validation surfaces an issue, the fix is scoped to the specific section/claim the
failing check identified (e.g. a `check_docs_structure.py` broken-link finding is a
local fix to that link) — unless the fix itself requires touching a different Task
scope row's content (e.g. a `check_docs_consistency.py --domain` drift finding that
traces back to what Step 5 actually changed), in which case Step 5's matching
procedure applies to that row as well. After fixing, re-run only the specific
checker(s) that failed to confirm the fix — not the full Step 6 checklist — then
proceed to Step 7. This fix-and-recheck loop is subject to AGENTS.md Attempt Limit (3
attempts per distinct failing checker); if a checker still fails after 3 fix attempts,
stop and report `Blocked: {checker} still failing after 3 attempts` rather than
continuing to patch.

## Step 7: Move the Completed Implementation Procedure File

This step MUST NOT be skipped.

This workflow's move to `implementations/done/` does not require human approval —
proceed once Steps 3, 4, and 6 pass, without stopping to ask the user for approval.
`rules/workflow-lifecycle.md` is scoped to `issue-to-plan`/`plan-to-impl-procedure`
only and does not apply to this workflow at all.

- Before attempting the move, check whether the destination
  `implementations/done/{filename}.md` already exists. If it does (e.g. Step 1's
  All-steps-completed check already moved this file earlier in the same session), do
  not attempt a second move — verify the source no longer exists at
  `implementations/{filename}.md` and treat the cycle as already archived.
- Do not perform this step before Step 5 (documentation update) and Step 6
  (documentation validation) are complete.
- Before proceeding, verify that:
  - the implementation procedure file's own `## Execution Status` section shows
    Completed for every step its template requires,
  - the final report's Execution Status section accurately reflects the actual work
    performed (completed items show Completed status, blocked items have blocker
    descriptions filled in, Work Items Created includes all artifacts produced).
- Prefer `uv run python tools/manage_workitem_stage.py close-implementation
  implementations/{filename}.md` — it performs the same `git mv` move and refuses
  (non-zero exit, no move) if the source is missing, the destination already
  exists, the source has uncommitted changes, or (redundantly, since this Step's
  own pre-check above already confirmed it) a `Pending` row remains. Fall back to
  the direct command below only if the tool is unavailable.
- Direct command (fallback): `git mv implementations/{filename}.md
  implementations/done/{filename}.md`. Do not use `mv`, `cp` + `rm`, or any other
  fallback beyond these two.
- Verify both: the file exists in `implementations/done/`, and the source no longer
  exists at `implementations/{filename}.md` — a move that leaves the file in both
  locations (a partial `git mv` failure) is not a completed move; treat it the same as
  a failed move below.
- **If the move fails, or leaves the file in both locations, stop and report
  `Blocked: move failed — {reason}`. Do not fall back to another method beyond the two
  above.**
  Report `Blocked` for this specific file only — its code/test/doc changes remain
  applied and validated, and its implementation procedure document remains generated
  but unarchived — then continue Multi-file processing with the next target file in
  the batch. Do not halt the entire batch because one file's Archival Move failed.

## Rollback on Failure

If implementation breaks existing functionality, revert changes immediately and
report `Blocked: {description}`. Per AGENTS.md Failure Log, record the failure details
(approach, error, reason) before considering a different approach. If reaching Attempt
Limit (3 attempts for the same error), the revert-and-report action is required.

After reverting, do not start a new implementation attempt for this same procedure
document in this session — a revert following 3 exhausted attempts is not itself a
"new approach" that resets the Attempt Limit (see `AGENTS.md` Loop Prevention >
Prohibit Repeating Failed Approaches). Stop this file's cycle here and wait for the
user to provide new information, approve a different scope, or explicitly direct a
retry — do not resume automatically once reverted.

## Final Report

**This cycle is complete when, and only when**: Step 7's move has succeeded and been
verified (both locations checked, per Step 7), or this file's cycle ended in a
per-file `Blocked` state per Step 3c/3e/4/6/7's own stop conditions (or Rollback on
Failure) — in either case, emit this Final Report once, then (per Multi-file
processing) begin Step 1 for the next target file, or end the batch if none remain.

Include the following in the final report:

### One-line traceability summary
`Source: {impl_proc_file} | Issue: {source_issue} | Plan: {source_plan} | Target: {related_target_files} | Changed: {files} | Completed: {timestamp from date +%Y%m%d-%H%M%S}`

`{source_issue}`, `{source_plan}`, and `{related_target_files}` are the values
extracted from the implementation procedure's own Traceability section in Step 2 —
carried forward, not re-derived. `{files}` is the changed-file list recorded in Step
3d's Execution Status Notes — read back from there, not recomputed from `git diff` at
report time.

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
render an empty table. Otherwise, use the Blocker Log table structure from
`templates/execution-status.md`.

### Work Items Created

If no artifact beyond the planned code/test/doc changes was produced, report `Work
items created: None` as a single line — do not render an empty table. Otherwise, use
the Work Items Created table structure from `templates/execution-status.md`.

## Output format

See `SKILL.md` Output format for the reporting structure to use — this phase does not
generate a single Markdown document with a fixed structure.
