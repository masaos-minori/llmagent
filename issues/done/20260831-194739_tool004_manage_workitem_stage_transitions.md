# Add `tools/manage_workitem_stage.py` to automate issue/plan/implementation-procedure stage moves and Execution Status updates

## Priority
Medium

## Summary
`skills/issue-to-plan` Step 10 and `skills/plan-to-implementation-procedure` Step 4 each require a
`git mv` of the processed file into its `done/` counterpart once validation passes, and an
implementation procedure's own Execution Status table is hand-edited to mark steps
Completed/Pending. All of this is currently done by directly editing files and running `git mv`
by hand, with no tool enforcing that the move only happens after its gating validation, or that
the Execution Status table is updated consistently.

## Background
This session performed several `git mv` operations for stage transitions (e.g., moving completed
implementation procedures into `implementations/done/`) and manually edited Execution Status
tables while doing so. `skills/issue-to-plan`'s Core Execution Rules state "No approval gate on
the archival move — it is gated on Step 9's validation passing instead" and "Move is required...
MUST NOT be skipped" — both are currently enforced only by an agent remembering to do them, not
by tooling.

## Reason for Change
A dedicated stage-transition tool turns a multi-step manual process (validate → `git mv` → edit
Execution Status table → verify) into one command, reducing the chance of a skipped move (leaving
a fully-processed issue/plan sitting outside its `done/` directory) or an Execution Status table
left inconsistent with what actually happened.

## Implementation Intent
Add `tools/manage_workitem_stage.py` with subcommands: `close-issue <issue-path>` (moves
`issues/{file}.md` to `issues/done/{file}.md` via the equivalent of `git mv`), `close-plan
<plan-path>` (moves `plans/{file}.md` to `plans/done/{file}.md`), and `close-implementation
<implementation-path>` (moves `implementations/{file}.md` to `implementations/done/{file}.md`).
Each subcommand should refuse to move a file whose own Execution Status table (for
implementation procedures) still has a `Pending` row, unless an explicit `--force` flag is passed
with a required `--reason`. This tool performs the mechanical move only — it does not decide
whether the underlying work is actually done; that judgment remains with the agent or human
invoking it.

## Target Files or Areas
- `tools/manage_workitem_stage.py` — new file
- `issues/`, `issues/done/`, `plans/`, `plans/done/`, `implementations/`, `implementations/done/`
  — the directories this tool moves files between
- `tools/TOOL_DESCRIPTIONS.md` — must document the new tool

## Required Changes
- Implement the three `close-*` subcommands using `git mv` (or the moral equivalent, preserving
  history) rather than a plain filesystem move.
- Parse the target file's Execution Status table (for `close-implementation`) and block the move
  if any row's Status is `Pending`, printing which rows are blocking, unless `--force --reason
  "..."` is supplied.
- Print a clear success/failure result, including the resulting path.

## Constraints
- Do not have this tool edit the substantive content of the file being moved beyond the move
  itself — it does not fill in or correct Execution Status rows, only reads them to decide
  whether to block.
- Do not perform the move via a plain filesystem rename if the repository is a git working tree —
  use `git mv` so history is preserved, consistent with every other stage-transition move
  documented in `skills/issue-to-plan`/`skills/plan-to-implementation-procedure`.
- Do not add a human-approval prompt — per `skills/issue-to-plan`/`skills/plan-to-implementation-procedure`,
  these archival moves are gated on validation, not on approval.

## Acceptance Criteria
- `close-issue`/`close-plan`/`close-implementation` each correctly `git mv` the target file into
  its `done/` counterpart.
- `close-implementation` refuses to move a file with a `Pending` Execution Status row unless
  `--force --reason` is given, and the refusal message names the blocking row(s).
- `tools/TOOL_DESCRIPTIONS.md` documents the new tool; `check_tool_descriptions_sync.py` passes.

## Testing Expectations
Add `tests/tools/test_manage_workitem_stage.py` using a temporary git repository fixture (not the
live repository) covering: a successful move for each of the three subcommands, a blocked move
due to a `Pending` row, and a forced move with `--force --reason`. Apply the standard validation
sequence in `rules/toolchain.md`.

## Documentation Impact
Add the new tool to `tools/TOOL_DESCRIPTIONS.md`.

## Out of Scope
- Deciding whether a plan or issue is actually ready to close — that judgment stays with the
  agent/human; this tool only performs the mechanical move and the Execution-Status gate check.
- The other four tools proposed alongside this one, tracked as separate issues.

## Dependencies
N/A: none — independently buildable. Complements
`tools/check_workitem_traceability.py` (tracked separately), which can report on files this tool
has not yet been used to close.

## Unresolved Questions
Whether `close-plan` should also verify that at least one implementation-procedure document
already references it as `Source plan` before allowing the move — needs an owner decision on
whether that check belongs here or solely in the separate traceability-checker tool, to avoid
duplicating validation logic in two places.

## AI Implementation Instruction
Read `skills/issue-to-plan/workflow.md` Step 10 and `skills/plan-to-implementation-procedure/workflow.md`
Step 4 in full before implementing the move logic, to match the exact pre/post-condition checks
those skills already define rather than inventing new ones. Use `git mv` (via subprocess or a git
library), not a plain filesystem rename.
