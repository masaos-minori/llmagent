# lifecyc001 stderr handle leaks on empty-command startup-failure path in SubprocessLauncher

## Priority
Low

## Summary
In `SubprocessLauncher.create_and_validate_proc`, the branch that raises
`HttpStartupError` when the spawned command is empty leaks the inherited
`stderr_fh` file handle and leaves a stale entry in `self._stderr_files`. The
success path and the non-empty-error path both clean these up; only the
empty-command failure path skips cleanup. This is currently locked by a
characterization test that asserts the leak is intentional.

## Background
`scripts/agent/http_lifecycle_subprocess_launcher.py` manages child processes
started via `subprocess.Popen`. On success it records the pipe in
`self._stderr_files` (line 82) and closes it in `finally` (line 91). On a
non-empty error it closes `stderr_fh` (line 68) and clears `self._stderr_files`
(line 69) before raising.

The empty-command guard (lines 72-79) raises `HttpStartupError` directly,
without closing `stderr_fh` or clearing `self._stderr_files`.

## Problem
When the command string is empty, `create_and_validate_proc` raises
`HttpStartupError` at line 76 without:
- closing the inherited `stderr_fh` (leaked for the lifetime of the launcher);
- clearing `self._stderr_files` (a dangling reference to a closed/closing pipe
  remains in the dict).

This is a minor resource leak and a state-consistency defect on a rare error
path. It does not affect the happy path or the normal error path.

## Reason for Change
Consistency: every other branch in this method cleans up both the handle and the
registry entry. The empty-command path is the only one that does not. Fixing it
removes the leak and keeps `self._stderr_files` consistent.

## Implementation Intent
Add the same cleanup the other branches perform before the empty-command
`raise HttpStartupError`: close `stderr_fh` and clear `self._stderr_files`.

## Target Files or Areas
- `scripts/agent/http_lifecycle_subprocess_launcher.py` — `create_and_validate_proc` (lines 72-79)
- `tests/agent/test_http_lifecycle.py` — characterization test at lines 223-249

## Required Changes
- Before raising `HttpStartupError` on the empty-command path, call
  `stderr_fh.close()` and set `self._stderr_files.clear()`, mirroring the
  non-empty-error branch (lines 68-69).
- Update the characterization test at `tests/agent/test_http_lifecycle.py`
  lines 223-249: it currently asserts
  `stderr_fh.close.assert_not_called()` and that the registry is untouched.
  Change the assertions to require the close and the clear (i.e. the leak is
  fixed), or remove the characterization lock if the intent is to stop
  asserting current behavior.

## Constraints
- Do not change the success-path or non-empty-error-path cleanup.
- Do not change what message `HttpStartupError` carries.
- Updating the characterization test is required and expected; it is not a
  violation of "don't change tests to hide bugs" because it documents a
  behavior change (leak -> no leak).

## Acceptance Criteria
- Raising `HttpStartupError` on an empty command closes `stderr_fh`.
- Raising `HttpStartupError` on an empty command clears `self._stderr_files`.
- `tests/agent/test_http_lifecycle.py` updated and passing.

## Testing Expectations
- Update the existing characterization test (or add a new one) asserting the
  close + clear on the empty-command failure path.
- Full suite in `tests/agent/test_http_lifecycle.py` passes.

## Documentation Impact
None beyond the test. No external docs.

## Out of Scope
- Any change to `Popen` construction, pipe setup, or the success path.
- Behavior of non-empty command errors.

## Dependencies
N/A: none

## Unresolved Questions
- Is the empty-command failure reachable in practice, or only via a malformed
  config? If unreachable, the leak is effectively dead code and the fix may be
  lower value — confirm whether to prioritize it.
- Should the characterization test be replaced with a regression test that pins
  the *fixed* behavior, or removed entirely?

## AI Implementation Instruction
In `create_and_validate_proc`, before `raise HttpStartupError(...)` on the
empty-command branch, add `stderr_fh.close()` and `self._stderr_files.clear()`
to match the other branches. Then update the characterization test at
`tests/agent/test_http_lifecycle.py` (lines 223-249) so it asserts the close and
clear instead of asserting they are skipped. Run the test suite and confirm it
passes.

## Traceability
- **Workflow phase**: `issue-creator` (fed by `python-code-review`)
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-220634
- **Related target files**: `scripts/agent/http_lifecycle_subprocess_launcher.py`, `tests/agent/test_http_lifecycle.py`
