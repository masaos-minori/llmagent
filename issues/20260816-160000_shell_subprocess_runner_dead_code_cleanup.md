# Confirm and clean up dead code in `shell/subprocess_runner.py` and `shell_service.py`

## Priority
Medium

## Summary
Several small, deferred cleanups from the `scripts/mcp_servers/shell/` subsystem's 2026-08-16
refactor cycles:
1. `SubprocessRunner.kill_timed_out_process` (a **public** method) appears to have zero
   production callers — `ShellService`'s only reference to it is via a method
   (`ShellService._kill_timed_out_process`) that itself has no callers anywhere in
   `run_command()`. The actual production kill-timeout path goes through
   `SubprocessRunner._kill_timed_out_process` (a *different*, private method) instead.
2. `SubprocessRunner.__init__` stores `timeout_sec` into `self._timeout_sec`, but it is never
   read anywhere in the class — the per-call timeout is always passed explicitly to
   `run_subprocess` instead.
3. `shell_service.py`'s module docstring references a stale filename ("`service.py`") instead of
   the current `shell_service.py`.

## Reason for Change
(1) and (2) were flagged as likely dead code but not removed because: `kill_timed_out_process`
is a **public** method, so removing it is a public-API change requiring the refactor procedure's
explicit-approval gate; and `_timeout_sec` was left alone specifically because the orchestrating
session flagged *all* timeout-related code in `subprocess_runner.py` as maximally
behavior-sensitive, not to be touched even for an apparently-safe dead-store removal, without
separate review. (3) is a trivial documentation-only fix, deferred only because the cycle's scope
was code-only.

## Implementation Intent
For (1): confirm via `rg "kill_timed_out_process"` across `scripts/` and `tests/` that there are
truly zero external callers (beyond the dead `ShellService._kill_timed_out_process` wrapper)
before removing either method. If confirmed dead, remove both
`SubprocessRunner.kill_timed_out_process` and `ShellService._kill_timed_out_process` together
(they're the same dead chain) — or, if there's a reason they exist (e.g. planned future use,
external plugin hook), document that reason instead of removing them.
For (2): confirm via `rg "_timeout_sec"` that no subclass or external caller reads the attribute,
then remove the dead store.
For (3): fix the docstring reference directly (no risk).

## Target Files or Areas
- `scripts/mcp_servers/shell/subprocess_runner.py` (`kill_timed_out_process`, `__init__`'s
  `self._timeout_sec`)
- `scripts/mcp_servers/shell/shell_service.py` (`_kill_timed_out_process`, module docstring)

## Required Changes
- `rg` confirm zero callers of `kill_timed_out_process`/`ShellService._kill_timed_out_process`
  repo-wide; if confirmed dead, remove both.
- `rg` confirm zero readers of `self._timeout_sec`; if confirmed dead, remove the attribute and
  its constructor parameter usage (only if the parameter itself becomes provably unused —
  otherwise just drop the unused store).
- Fix `shell_service.py`'s module docstring filename reference.

## Acceptance Criteria
- If removed: `tests/mcp_servers/shell/` full suite (54+ tests) passes unchanged; no import
  errors; `rg` confirms zero remaining references to the removed symbols.
- If kept: an inline comment documents why, referencing this issue.
- Module docstring in `shell_service.py` references the correct current filename.

## Testing Expectations
Full `tests/mcp_servers/shell/` regression suite before and after any removal;
`tests/mcp_servers/cicd/test_tool_server_layer_consistency.py` (constructs `ShellService`
directly) must also pass unchanged.

## Documentation Impact
None expected beyond the docstring fix itself (item 3).

## Out of Scope
- Do not change `SubprocessRunner._kill_timed_out_process` (the private, actually-used
  policy-aware kill path) — it is out of scope and already covered by characterization tests.
- Do not remove anything without first confirming via `rg` that it is genuinely unreferenced.

## AI Implementation Instruction
Run the `rg` confirmation searches for items (1) and (2) and report the exact results before
removing anything — if either search surfaces even one unexpected caller, stop and report rather
than removing the code. Item (3) (docstring fix) can be done immediately with no risk.
