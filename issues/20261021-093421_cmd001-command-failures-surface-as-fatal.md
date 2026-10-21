# Slash-command failures surface as `[fatal]` with no usage hint or partial-effect statement

## Priority
Medium

## Summary
Give command dispatch its own error surface so a failed command is reported as a command error, not as a
turn-level fatal failure.

## Background
`CommandRegistry.dispatch()` has no error handling (`scripts/agent/commands/registry.py:115-137`):
`_invoke_handler` (`:105-113`) calls the handler and any exception propagates.
`ReplInputLoop._dispatch_line` (`scripts/agent/repl_input_loop.py:213-217`) does not catch it either, so
the per-turn `except Exception` in `_repl_loop` (`:311-312`) handles it, and `_surface_turn_error` renders
`self._view.write_fatal(f"{exc.__class__.__name__}: {exc}")` (`:128-134`) — the `[fatal]` tag
(`scripts/agent/output_tags.py:14-18`).

## Problem
- A command error and a turn failure share one output channel and one tag. `FATAL`, `NON_FATAL`, `ERROR`,
  and `USAGE` all exist as distinct severities, and `write_error`/`write_usage` exist on the view
  (`scripts/agent/cli_view.py:239-241`), but no command path uses them for a dispatch failure.
- No command module handles database errors: `grep -rn 'sqlite3|OperationalError|IntegrityError'
  scripts/agent/commands/` matches nothing, so a `sqlite3.Error` from `/session delete`, `/session purge`,
  `/memory prune`, or `/session vacuum` surfaces as `OperationalError: …` with no explanation of which
  subcommand failed or whether anything changed. Several of these mutate state before failing, so partial
  effects are invisible.
- The exception type name is the only message. For an operator this is unreadable and it is not attributable
  to a command in the logs.
- Unknown-command handling is the one place that does behave correctly (`:215-218` writes a warning with a
  `/help` hint), which shows the intended pattern is a command-scoped message.

## Reason for Change
Commands are the operator's main interface. Reporting an input or storage problem as a fatal turn failure
makes an ordinary mistake look like a session-ending error and hides what actually went wrong.

## Implementation Intent
Handle command dispatch errors at the command boundary: classify them as command errors, render them with
the existing error/usage severities, and name the subcommand that failed.

## Target Files or Areas
- `scripts/agent/commands/registry.py` (`dispatch`, `_invoke_handler`)
- `scripts/agent/repl_input_loop.py` (`_dispatch_line`, `_surface_turn_error`)
- `scripts/agent/cli_view.py`, `scripts/agent/commands/output_port.py` (severity mapping)
- `scripts/agent/commands/db_session_ops.py`, `cmd_session.py`, `cmd_memory.py` (DB error cases)

## Required Changes
- Catch handler exceptions in `dispatch()` (or in `_dispatch_line` for the command branch only) and render
  them through `write_error`/`write_usage` with the command name and its usage string.
- Map storage errors to a command-level message that states the subcommand and that the effect may be
  partial.
- Keep `_surface_turn_error` for actual turn failures only.
- Log the attributed command error so it is traceable.

## Constraints
- Do not change the `[fatal]` semantics for turn-level failures.
- Do not swallow exceptions silently; every handled error must produce a message and a log entry.
- `dispatch()`'s `bool` return contract and its `TypeError` guard (`registry.py:122-123`) must stay.
- Command output formatting is shared with tests that assert exact prefixes; keep existing tag strings.

## Acceptance Criteria
- A command handler that raises produces `[error]` (or `[usage]`) output naming the command, and produces
  no `[fatal]` line.
- A turn failure still produces `[fatal]`.
- A forced DB error in `/session delete` reports the subcommand and that the session may be unchanged.
- The handled error appears in the agent log with the command name.

## Testing Expectations
- Regression tests: a command handler that raises, asserting the tag and the presence of the command name;
  a turn-failure test asserting `[fatal]` is still used.
- Keep the assertions on tags, not on message bodies, to avoid brittle text coupling.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document the error taxonomy for REPL output (`[fatal]` vs `[error]` vs `[usage]` vs `[non-fatal]`) and
which component emits each, in the CLI/commands docs. Note that command errors are not turn failures.

## Out of Scope
- Argument parsing and validation rules (`cmd002`).
- Event-loop blocking in command handlers (`cmd003`).
- Adding new commands or changing command output layouts.

## Dependencies
- Review together with `cmd002`: validation errors are the most common case this issue changes how they
  are reported.

## Unresolved Questions
- Should a failed command be recorded in the audit log as well as the agent log? Needs confirmation.
- Is there an existing documented severity contract in `docs/23_agent/` that this issue must match? Needs
  confirmation before choosing tags.

## AI Implementation Instruction
Handle errors where the command boundary is, not in the REPL loop. Do not introduce a new exception
hierarchy beyond what is needed to name the failing command.

## Traceability
- **Workflow phase**: `python-code-review` (command dispatch review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/commands/registry.py`, `scripts/agent/repl_input_loop.py`,
  `scripts/agent/cli_view.py`, `scripts/agent/commands/output_port.py`
