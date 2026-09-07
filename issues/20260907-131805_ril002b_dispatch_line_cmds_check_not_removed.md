# Fix implementation-procedure/code mismatch: `_dispatch_line`'s duplicate `_cmds` check was never removed

## Priority
Medium

## Summary
`implementations/done/20260904-101242_01_scripts_agent_repl_input_loop_py.md` — the archived
implementation procedure for `issues/done/20260904-001051_ril002_cmds_check_consistency.md` —
records its Step 1 ("Remove duplicate `_cmds` check from `_dispatch_line`") as `Completed`, with
the note "Single authoritative check remains in `_repl_loop`". Direct read of the current
`scripts/agent/repl_input_loop.py` shows this change was never applied: `_dispatch_line` still
contains its own `if self._cmds is None:` check (line 183), independent of `_repl_loop`'s check
(line 202), and the class docstring still claims `_repl_loop` is "the single authoritative
precondition" (line 41) — a claim the code contradicts.

## Background
`Explicit in code`: `scripts/agent/repl_input_loop.py:183` (`_dispatch_line`) and `:202`
(`_repl_loop`) each independently execute `if self._cmds is None: raise RuntimeError(...)`. The
implementation procedure document's own "Method > Step 1" instructed changing lines 170-171
(the pre-edit line numbers) "to nothing (remove these two lines entirely)" and its Execution
Status table marks this Completed. The current line numbers differ from the procedure's cited
170-171 only because of the intervening docstring insertion (Step 2, which *was* applied — the
"`_cmds` lifecycle" docstring block is present at lines 38-41) — the file was edited, but Step
1's specific removal did not take effect while Step 2's docstring addition did.

## Problem
An implementation procedure archived in `implementations/done/` records a specific line-level
code change as `Completed` that is not present in the current source. This is a record-integrity
gap distinct from ordinary unimplemented backlog: the archive states work was done that verifiably
was not, which risks anyone trusting `implementations/done/`'s status without re-reading the code
(exactly as this repository's own audit history around `plans/done/`/`issues/done/` has already
flagged as a recurring risk).

## Reason for Change
The original REQ-RIL002-1 ("single authoritative check for `_cmds` availability") remains unmet,
and the docstring added by the same procedure now actively misdescribes the code (claiming a
single authoritative check exists when two independent checks remain). Both the functional gap
and the docstring/code mismatch should be fixed together since they were meant to land together.

## Implementation Intent
Apply the originally-specified fix: remove `_dispatch_line`'s independent `_cmds is None` check
(line 183) since `_dispatch_line` is only ever called from within `_repl_loop`'s loop, which
already checks this precondition first. Keep the existing docstring's claim accurate by making
the code match it, not by softening the docstring's wording.

## Target Files or Areas
- `scripts/agent/repl_input_loop.py` (`_dispatch_line` line 183, `_repl_loop` line 202, class
  docstring lines 38-41)

## Required Changes
- Remove the `if self._cmds is None: raise RuntimeError(...)` block from `_dispatch_line`.
- Confirm `_dispatch_line` is never called on a path that bypasses `_repl_loop`'s precondition
  check (e.g. directly from a test or another caller) before removing its check — if such a path
  exists, report it rather than removing the check.
- Preserve `_repl_loop`'s existing check and its `RuntimeError` message text unchanged.

## Constraints
- Must not change the runtime behavior of command dispatch for any currently-valid call path.
- Must preserve the safety guarantee that `_cmds` is always available during dispatch.

## Acceptance Criteria
- [ ] `scripts/agent/repl_input_loop.py`'s `_dispatch_line` no longer contains an independent
      `_cmds is None` check.
- [ ] Exactly one `_cmds is None` check remains in the file (`_repl_loop`).
- [ ] The class docstring's "single authoritative precondition" claim is accurate against the
      resulting code.
- [ ] No regression in existing REPL command-dispatch tests.

## Testing Expectations
Run the existing REPL input-loop test suite (locate via `rg -l "ReplInputLoop\|repl_input_loop"
tests/`) to confirm no regression; add a test only if none currently exercises `_dispatch_line`
being called before `_cmds` initialization.

## Documentation Impact
None beyond the class docstring already covered in Required Changes — no `docs/*.md` file
references this internal check.

## Out of Scope
- Any other REPL command dispatch behavior change.
- Re-verifying REQ-RIL002-2 (the immutability-contract docstring itself), which is already
  present and accurate.

## Dependencies
N/A: none — this is a self-contained correction to a single file, re-applying the already-decided
design from `issues/done/20260904-001051_ril002_cmds_check_consistency.md` and
`implementations/done/20260904-101242_01_scripts_agent_repl_input_loop_py.md`.

## Unresolved Questions
N/A: none — the fix (remove `_dispatch_line`'s check) was already decided by the archived
implementation procedure; this issue only re-files its non-applied step.

## AI Implementation Instruction
Before editing, re-read `scripts/agent/repl_input_loop.py` in full and re-confirm both check
sites via `rg -n "_cmds is None" scripts/agent/repl_input_loop.py`, since line numbers here may
have shifted. Verify `_dispatch_line` has no caller that bypasses `_repl_loop` (check tests
directly invoking `_dispatch_line`) before removing its check — if one exists, stop and report
rather than removing the check.
