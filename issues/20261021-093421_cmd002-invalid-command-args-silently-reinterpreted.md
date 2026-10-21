# Invalid command arguments are silently reinterpreted instead of rejected

## Priority
High

## Summary
Make numeric command arguments validate once, consistently, and reject out-of-range or malformed values
with a usage error instead of substituting a default.

## Background
Numeric argument handling is implemented separately per command group:
`scripts/agent/commands/cmd_context.py:138-145` (`/history`), `cmd_session.py:83-88`
(`/session list [n]`), `cmd_session.py:43-52` (`_parse_positive_session_id`),
`db_session_ops.py:11-16` (`_parse_optional_int`), and `memory_data_ops.py:84-91`, `:135-149`
(`/memory list`, `/memory prune --days`).

## Problem
- `/history [n]` accepts any integer and slices with it: `recent = turns[-n:]`
  (`cmd_context.py:147-148`). `/history 0` prints "No conversation history." and
  `/history -3` evaluates `turns[3:]` — it prints the oldest `len-3` messages instead of the last 3. No
  range check exists, while the sibling command `/memory list` rejects `n < 1` and `n > 200` with a
  validation error (`memory_data_ops.py:85-89`).
- `/session list abc` is silently rewritten to 20 (`cmd_session.py:85-87`: `except (ValueError, TypeError):
  limit = 20`), so a typo produces a plausible-looking list rather than an error.
- `_parse_optional_int` cannot distinguish "not given", "invalid", and `0`: `return int(raw) if raw else
  None` (`db_session_ops.py:13-14`). `/session purge --max-sessions 0` therefore becomes `None` —
  "no limit" — and is passed to `DbMaintenanceService().purge(...)` (`db_session_ops.py:53-55`), so a
  value intended to limit a destructive operation is inverted into the unbounded case. `--max-age-days abc`
  and `--max-age-days 0` are indistinguishable and both fall back to the retention default.
- Because `/session` and `/memory` are prefix commands, the raw remainder is handed to the handler as one
  string (`registry.py:124-129`) and each handler re-implements its own parsing, which is why the rules
  differ per command.

## Reason for Change
Silent reinterpretation makes operator mistakes invisible, and in the `/session purge` case it changes the
amount of data a destructive maintenance command removes.

## Implementation Intent
Validate numeric arguments at one place with one rule set: reject non-integers, reject out-of-range, and
never substitute a default for an explicitly invalid value.

## Target Files or Areas
- `scripts/agent/commands/cmd_context.py` (`_cmd_history`)
- `scripts/agent/commands/cmd_session.py` (`_session_list`)
- `scripts/agent/commands/db_session_ops.py` (`_parse_optional_int`, `purge`)
- `scripts/agent/commands/memory_data_ops.py` (the pattern to reuse)
- `scripts/agent/commands/command_defs_list.py` (`SubcommandSpec` usage strings)

## Required Changes
- Add a range check for `/history [n]` (or bound the slice), consistent with `/memory list`.
- Make `/session list` report a validation error for a non-numeric limit instead of defaulting.
- Separate "flag absent" from "flag invalid" in `_parse_optional_int`, and reject `0` where `0` is not a
  meaningful value; state which values are valid for `--max-sessions` and `--max-age-days`.
- Reuse one argument-parsing helper for numeric flags rather than per-command parsers.
- Keep the usage text in `SubcommandSpec` in sync with the accepted range.

## Constraints
- Existing valid usages (`/history` with no argument, `/session list` with no argument, `/session purge`
  with no flags) must behave exactly as today.
- Do not change what `DbMaintenanceService.purge` accepts; validate before calling it.
- Error text must follow the tag rules decided in `cmd001`.
- Existing tests that rely on the current defaults must be updated deliberately, not silently.

## Acceptance Criteria
- `/history 0`, `/history -3`, `/session list abc`, `/session purge --max-sessions 0`, and
  `/session purge --max-age-days abc` each produce a validation error naming the expected form.
- Omitting the argument keeps today's default behavior.
- One shared numeric-parsing helper is used by the affected commands; no per-command `int()` fallback to a
  default remains.

## Testing Expectations
- Table-driven tests over invalid and omitted values per command, asserting either the documented default
  or a validation error.
- A test asserting `/session purge --max-sessions 0` does not run the unbounded purge.
- `uv run pytest tests/agent -q`, `uv run ruff check scripts/agent`,
  `uv run mypy --no-namespace-packages scripts/agent`.

## Documentation Impact
Document each command's accepted argument ranges in the CLI/commands reference and in the command
`SubcommandSpec` help text, and state the general rule: an invalid argument is an error, a missing argument
may use a documented default.

## Out of Scope
- Command error tagging and dispatch-level error handling (`cmd001`).
- Adding new flags or new subcommands.
- The retention policy defaults themselves.

## Dependencies
- Pairs with `cmd001`, which decides how a validation error is displayed.
- Independent of `cmd003`.
- Related to `20261020-123319_compat008_classify-the-session-export-md-alias-and-define-the-rule-for-command-aliases.md`:
  that issue defines the command alias/subcommand naming rule. Not a duplicate — this issue covers numeric
  argument validation only — but the shared argument-parsing helper must not contradict that rule.

## Unresolved Questions
- Is `0` a meaningful value for `--max-sessions` / `--max-age-days` (i.e. "delete nothing") or invalid?
  Needs confirmation with the retention semantics in `DbMaintenanceService.purge`.
- Is there a documented upper bound for `/history`? Needs confirmation.

## AI Implementation Instruction
Validate before use, never coerce invalid input to a default. Centralize the numeric parsing so the rules
are stated once.

## Traceability
- **Workflow phase**: `python-code-review` (command dispatch review), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261021-093421
- **Related target files**: `scripts/agent/commands/cmd_context.py`, `scripts/agent/commands/cmd_session.py`,
  `scripts/agent/commands/db_session_ops.py`, `scripts/agent/commands/memory_data_ops.py`
