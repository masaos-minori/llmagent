# Code Implementation — Edge Cases

Sections of `workflow.md` that apply only to a minority of cycles, moved here verbatim. Load
this file only when the trigger written in the matching place of `workflow.md` holds, and
follow the section it names. The main workflow keeps every heading, so a citation by section
name still resolves there.


### Batch mode (plan batch)

Applies when one run covers two or more procedures with the same `Source plan` that are not
members of a declared release unit (a declared unit uses Batch mode (release unit), which takes
precedence for its members). A run holding one procedure of a Plan keeps the per-cycle gate and
per-file archival. The procedures of one Plan are one change split per file in `seq` order: a
cycle can leave the suite red until a later procedure lands (for example a default removed in
`seq` 01 whose call sites change in later procedures), and a full-suite run per procedure
repeats the same run once per member.

Explicit exceptions, stated per `rules/ai-execution.md` Instruction Precedence > Explicit
exceptions, for a plan batch only:
- Step 4's full-suite run and the diff-cover gate run once per plan batch, after the last member
  that completed Steps 1-6, instead of once per cycle.
- `rules/ai-execution.md` Sequential Target Processing (Base), "Complete its full workflow
  cycle and required gates before loading the next target", is excepted for the full suite, the
  diff-cover gate, and Step 7 only; every other step and gate completes per member.

Per member, in `seq` order: Steps 1-3e, 5 and 6 run as usual, and Step 4's impact-selected
targeted tests still run and MUST pass. Unlike a declared unit there are no allowed red states:
a targeted-test failure or a Step 3e finding stops the cycle under the Attempt Limit (3
attempts) and Failure Log. A member's own Execution Status row 3 stays `In Progress` until the
end-of-batch run passes. A member that ends `Blocked` or by Rollback stops the rest of its Plan
(Dependency order).

End of batch: run the full suite with coverage and diff-cover once (Step 4) over the completed
members. On failure the Attempt Limit applies, and Rollback on Failure covers the files recorded
in the members' Notes; a path changed by more than one member is reported, not reverted. When a
member ended `Blocked` and the failure is attributed to a symbol that member would have created,
report `Blocked` for the batch without a rollback and ask (Question policy). Once the run
passes, run Step 7 for every completed member with `--stage-only`, then the Plan Execution
Status update.

**Resume.** A member of a plan batch (or of a release unit) that finished Steps 1-6 keeps row 3
`In Progress` with every other row `Completed`, and its changed files stay uncommitted in the
working tree; the changed-file list is in its Notes (Step 3d). A new run that finds such a
member in `implementations/` treats it as awaiting the end-of-batch run: it does not redo the
member's Steps 1-6, and Step 1's Partial-completion resume does not restart it. The unfinished
members run Steps 1-6 in `seq` order, then the end-of-batch run covers every member, awaiting
and new; when only awaiting members remain, go straight to that run. Before running it, check
that each awaiting member's recorded files still show as modified in `git status --short`; if
one no longer does (committed or reverted by another writer), stop and ask (Question policy)
rather than running the end-of-batch run on a changed premise.

### Batch mode (release unit)

Applies only when the procedures of one `Source plan` carry the same unit name on the
`Release unit` line of `## Scope` (the Plan's `### Release units` entry names the members and
why they cannot be validated alone). If only part of a unit is in the batch, stop and ask
(Question policy) rather than running a half unit in ordinary mode. A Plan without a unit,
and any procedure whose line is `N/A: not part of a release unit`, is handled by Batch mode (plan
batch) when the run holds two or more procedures of its Plan, and otherwise keeps the per-cycle
gate and per-file archival.

Explicit exceptions, stated per `rules/ai-execution.md` Instruction Precedence > Explicit
exceptions, for a declared unit only:
- Step 4's full-suite run (`workflow.md`) runs once per unit, after the last member.
- `rules/ai-execution.md` Sequential Target Processing (Base), "Complete its full workflow
  cycle and required gates before loading the next target", is excepted for the full suite,
  the diff-cover gate, and Step 7 only; every other step and gate completes per member.

Per member, in `seq` order: Steps 1-3e, 5 and 6 run as usual, and Step 4's impact-selected
targeted tests still run. Allowed red states, each recorded in the Failure Log with the
reason: (a) a targeted test failure, or (b) a Step 3e finding (type, import), that the
executor attributes to a symbol or schema a later member creates. Every other failure stops
the cycle under the Attempt Limit (3 attempts) and Failure Log. Step 3d's baseline check and
single-path Rollback on Failure still apply, limited to files recorded in the members' Notes;
a fix that touches an already finished member's file adds that file to the Notes list. A
member's own Execution Status row 3 stays `In Progress` until the end-of-unit run passes.

End of unit: after the last member, run the full suite with coverage and diff-cover once
(Step 4); on failure the Attempt Limit applies. Once it passes, run Step 7 for every member
with `--stage-only`, then the Plan Execution Status update.

### Step 1 edge cases

- **All-steps-completed check**: after reading the file, inspect its `## Execution Status`
  table. If every step row shows `Completed` (no `Pending`, `Blocked`, or other status),
  the procedure is fully executed — MUST NOT re-execute it. Move it to
  `implementations/done/` (same rules as Step 7): prefer `uv run python
  tools/manage_workitem_stage.py close-implementation implementations/{filename}.md`;
  fall back to `git mv implementations/{filename}.md implementations/done/{filename}.md`
  only if the tool is unavailable. Verify the file exists in `implementations/done/`
  after the move. Report
  `Moved to done: {filename} — all steps Completed, no further action needed`.
  Then apply Step 7's Plan Execution Status update if the Plan rows for this file are not
  yet `Completed`. If this move fails, the same continuation policy applies: report
  `Blocked` for this file only and continue to the next target file in the batch (see
  Step 7).
- **Partial-completion resume**: if at least one row is `Completed` but not all
  (a resumed, previously-interrupted cycle), resume from the first Step whose row is
  not `Completed`. The exception is a member left awaiting a batch's end-of-batch run
  (row 3 `In Progress`, every other row `Completed`): it is not a cycle to resume, see
  Multi-file processing > Batch mode (plan batch), Resume. MUST NOT re-run a Step already marked `Completed` unless a later
  Step's Adversarial Verification (Step 3a) specifically finds that Step's output is
  now stale. MUST NOT re-derive or re-verify a `Completed` Step's conclusion merely
  because the cycle is resuming.
- **Superseded procedure**: when the procedure's design no longer matches live code
  (another change landed first, or a duplicate procedure covers it) and the user has
  decided not to implement it, do not execute it. Archive it with `uv run python
  tools/manage_workitem_stage.py close-implementation implementations/{filename}.md
  --superseded --reason "{why}"`: every unfinished row becomes `Superseded` with the reason
  in its Notes, so the archive does not claim the work was done. A procedure whose rows are
  `Superseded` is never resumed; archive it with the same command. MUST NOT move it with
  `git mv` (that leaves `Pending` rows in `implementations/done/`, which
  `tools/check_workitem_structure.py --archived-status` reports) and MUST NOT mark rows
  `Completed` for work that was not done. Report `Superseded: {filename} - {reason}`, then
  run `uv run python tools/sync_plan_workitem_status.py {plan_path}` so the Plan row reads
  `Superseded`.

### Plan Execution Status update: manual path

- **Manual path** (the command is unavailable or refused, or the procedure was already moved
  with `close-implementation`): after the move succeeds, update the source Plan's own
  Execution Status and set the procedure's `Work Items Created` row to `Completed` by direct
  edit. Read
  this implementation procedure's Traceability `Source plan` and `Related target
  files` values (already extracted in Step 2) and locate that Plan file (it may already
  be in `plans/done/` if `plan-to-implementation-procedure` archived it before this
  cycle ran). The Plan's Execution Status has one row per `Implementation steps`
  entry (same numbering), not one per target file, and each step cites the
  `File Path`(s) it touches. So map by step number, and only for steps that modify a
  cited file: a step that only runs checks or gates, records a baseline, deploys, or
  waits for a user decision is not completed by archiving a procedure, so leave its row
  as it is. For each step N that modifies this cycle's target file, set row N to
  `Completed` only when every file that step N modifies has its procedure archived
  (this cycle's included — check `implementations/done/` for a document with the same
  `Source plan` and that file as `Related target files`); a file counts as having its
  procedure archived when it is the target or a companion of such a document, so a step
  that cites only a companion test file is `Completed` with its code row's archive;
  otherwise leave row N as it is. Use `uv run python
  tools/manage_workitem_stage.py set-step-status plan {plan_path} --step {N} Completed
  --completed {timestamp from date +%Y%m%d-%H%M%S}` — not `--description`, which
  updates only the first row whose Description merely contains the given text. If
  `close-batch` was run on this batch outside this workflow, re-check every row it marked:
  it overwrites all of them, so rows for work that was not done must be set back with
  `set-step-status`. If `Source plan` is `N/A` (no Plan produced this
  procedure document), skip this update — there is no Plan row to close. If the Plan
  file cannot be found at either location, report this as a non-blocking Note in the
  Final Report (`Plan Execution Status not updated: {reason}`) rather than treating
  it as a cycle failure — the implementation procedure's own move has already
  succeeded and MUST NOT be reverted or blocked on this secondary update.

## Rollback on Failure

If implementation breaks existing functionality, revert changes immediately and
report `Blocked: {description}`. Also apply the procedure's `## Rollback considerations` (for example a step that is not a
file edit). Revert only this cycle's own changes, using the changed-file list recorded in
Step 3d's Execution Status Notes (plus any test/doc file this cycle edited). Every such
path was clean in Step 3d's baseline (a modified one stopped the cycle before editing),
so a single-path revert cannot discard another writer's changes. For each tracked
file, run `git checkout -- <path>` on that single path; for a file this cycle created,
delete that single file. MUST NOT use a bulk form (`checkout -- .`, `restore .`,
`reset --hard`, `clean`). In a batch, earlier cycles' changes are still uncommitted
(Step 7's `--stage-only`), so if a path to revert was also changed by an earlier cycle in
the same batch, MUST NOT revert it — stop and report `Blocked: {path} also changed by
{earlier file}`, and let the user decide. Per AGENTS.md Failure Log, record the failure details
(approach, error, reason) before considering a different approach. At the Attempt
Limit (3 attempts for the same error), revert-and-report is required.

After reverting, MUST NOT start a new implementation attempt for this same procedure
document in this session (see `AGENTS.md` Loop Prevention > Rollback Directive). Stop
this file's cycle here and wait for the user to provide new information, approve a
different scope, or explicitly direct a retry — MUST NOT resume automatically once
reverted.
