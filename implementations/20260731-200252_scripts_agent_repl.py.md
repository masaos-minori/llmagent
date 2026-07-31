# Implementation Procedure: Fix Windows Signal Handler Race in REPL

## Goal
Fix Windows signal handling by removing unnecessary `isatty()` check and ensuring signal handlers are installed from the main thread.

## Scope
- `scripts/agent/repl.py`

## Assumptions
- Removing the `isatty()` check will not prevent legitimate console control handler installation on Windows.
- All signal handler installations must happen on the main thread to avoid race conditions.

## Design decisions
- Remove the `sys.stdout.isatty()` check in the fallback Windows signal handler registration.
- Ensure all `signal.signal()` calls are executed within the main thread context.

## Alternatives considered
- N/A

## Implementation
### Target file
`scripts/agent/repl.py`

### Procedure
1. Modify `AgentREPL.run` to remove the `sys.stdout.isatty()` check when attempting to register the Windows console control handler.
2. Audit `AgentREPL.run` and other methods to ensure `signal.signal()` and `win32api.SetConsoleCtrlHandler` are only invoked from the main thread.

### Method
Code modification and threading analysis.

### Details
The current code restricts Windows signal handling to cases where `sys.stdout.isatty()` is true. This may miss some terminal environments. Removing this check allows broader support. Additionally, verifying thread safety for signal registration prevents intermittent race conditions during shutdown.

## Compatibility considerations
- No impact on Unix-based systems which use `loop.add_signal_handler`.

## Security considerations
- N/A

## Rollback considerations
- Revert the changes to the conditional check in `AgentREPL.run`.

## Validation plan
- Run the REPL on Windows in various terminal emulators (CMD, PowerShell) and verify that `SIGINT`/`SIGTERM` triggers a graceful shutdown.
- Perform regression testing on Linux/macOS to ensure standard signal handling is unaffected.

## Out of scope
- N/A

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260731-0754_require.md
- Source plan: plans/20260731-090405_plan.md
- Source implementation procedure: N/A
- Generated at: 20260731-200252
- Related target files: scripts/agent/repl.py
