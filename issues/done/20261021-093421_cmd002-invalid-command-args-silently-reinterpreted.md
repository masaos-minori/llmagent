# Invalid command arguments are silently reinterpreted instead of rejected

## Priority
High

## Summary
Make numeric command arguments validate once, consistently, and reject out-of-range or malformed values
with a usage error instead of substituting a default.

## Background
Numeric argument handling is implemented separately per command group:
`scripts/agent/commands/cmd_context.py:138-146` (`/history`), `cmd_session.py:77-88`
(`_session_list`, reached from `:187-189`), `cmd_session.py:43-54` (`_parse_positive_session_id`),
`db_session_ops.py:11-16` (`_parse_optional_int`), `db_session_ops.py:50-55` (`purge`), and
`memory_data_ops.py:85-91`, `:128-149` (`/memory list`, `/memory prune --days`).
`scripts/agent/commands/utils.py:59-76` already holds two numeric flag helpers (`parse_flag_int`,
`parse_flag_str`) that no command calls (`grep -rn "parse_flag_int\|parse_flag_str" scripts tests`
matches only their definitions and `__all__`), so a fourth rule set is what today's per-command parsers
would add.

## Problem
- `/history [n]` accepts any integer and slices with it: `n = int(raw)` at `cmd_context.py:142-143`,
  `recent = turns[-n:]` at `:149`. `/history 0` evaluates `turns[-0:]`, which is `turns[0:]` — it prints
  every message, not "No conversation history." (that message appears only when the history holds no
  user/assistant message). `/history -3` evaluates `turns[3:]` and prints the oldest `len-3` messages
  instead of the last 3. No range check exists, while the sibling command `/memory list` rejects `n < 1`
  and `n > 200` with a validation error (`memory_data_ops.py:85-91`).
- `/session list abc` is silently rewritten to 20 (`cmd_session.py:85-87`: `limit = int(limit_arg) if
  limit_arg else 20` then `except (ValueError, TypeError): limit = 20`), so a typo produces a
  plausible-looking list rather than an error. A negative value is not rejected either: it reaches
  `Session.list_sessions`'s `LIMIT ?` (`scripts/agent/session.py:175-185`), where SQLite treats a negative
  limit as unlimited and `LIMIT 0` as no rows.
- `_parse_optional_int` cannot distinguish "not given" from "invalid", and treats a bare flag as a value:
  `return int(raw) if raw else None` (`db_session_ops.py:13-14`). Verified against the retention
  implementation (`scripts/db/maintenance.py`):
  - `/session purge --max-sessions 0` keeps `0` (`"0"` is a truthy string), so
    `_delete_sessions_beyond_limit` (`maintenance.py:185-202`) deletes **every** session — the maximally
    destructive case, not "no limit".
  - `/session purge --max-sessions` with no value parses as `True` (the shared `parse_command_args` sets
    a bare flag to `True`, `utils.py:43-50`) and `int(True)` is `1`, so the command keeps exactly one
    session.
  - A negative value is not rejected either, and the two flags interpret the same sign oppositely:
    `len(rows) <= -3` is never true, so `--max-sessions -3` deletes `rows[-3:]` — the **3 oldest**
    sessions (`maintenance.py:186-190`, `ORDER BY created_at DESC`) — while `--max-age-days -5` is
    treated as "disabled" (`maintenance.py:167-170`).
  - `None` (flag absent) is what selects the `RetentionConfig` defaults (`max_sessions=100`,
    `max_age_days=90`, `maintenance.py:104-105`) via `_build_retention_config`
    (`scripts/agent/services/db_maintenance_service.py:87-96`); any parsed int is passed through
    unchanged (`db_maintenance_service.py:64-74`).
  - `--max-age-days abc` falls back to `None` → `RetentionConfig` default 90 (`maintenance.py:104-105`),
    while `--max-age-days 0` disables age-based deletion (`maintenance.py:169-170`). They are
    distinguishable, and `0` is a documented meaningful value for `max_age_days` only
    (`maintenance.py:102`: "0=disabled").
- The accepted token set also differs per command: `/memory list` requires `tok.isdigit()`
  (`memory_data_ops.py:85`), which accepts non-ASCII digits such as `'٣'` and rejects `'+5'`, `'1_0'` and
  `' 5 '`, while the other four paths use `int()`, which accepts them.
- Because `/session` and `/memory` are prefix commands, the raw remainder is handed to the handler as one
  string (`registry.py:128-131`) and each handler re-implements its own parsing, which is why the rules
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
- Reuse one argument-parsing helper for numeric flags rather than per-command parsers, and do not leave a
  second numeric parser in the tree: `utils.py`'s unused `parse_flag_int` has the same
  parse-or-fall-back-to-default shape and must be removed or replaced by that helper.
- Keep the usage text in `SubcommandSpec` in sync with the accepted range.

## Constraints
- Existing valid usages (`/history` with no argument, `/session list` with no argument, `/session purge`
  with no flags) must behave exactly as today.
- Do not change what `DbMaintenanceService.purge` accepts; validate before calling it.
- Error text must follow the tag rules decided in `cmd001`.
- Existing tests that rely on the current defaults must be updated deliberately, not silently.

## Acceptance Criteria
- `/history 0`, `/history -3`, `/session list abc`, `/session purge --max-sessions 0`,
  `/session purge --max-sessions` (no value), and `/session purge --max-age-days abc` each produce a
  validation error naming the expected form.
- Omitting the argument keeps today's default behavior, and `--max-age-days 0` keeps its documented
  "disabled" meaning.
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
- Related to `issues/done/20261020-123319_compat008_classify-the-session-export-md-alias-and-define-the-rule-for-command-aliases.md`
  (archived): that issue defines the command alias/subcommand naming rule. Not a duplicate — this issue
  covers numeric argument validation only — but the shared argument-parsing helper must not contradict that
  rule.

## Unresolved Questions
- Is `0` a meaningful value for `--max-sessions` / `--max-age-days` (i.e. "delete nothing") or invalid?
  Resolved against the retention implementation: for `max_age_days`, `0` is documented as "disabled"
  (`scripts/db/maintenance.py:102`, honored at `:169-170`), so it is a valid value. For `max_sessions`
  there is no documented `0` semantics and `0` deletes every session (`:185-202`), so it must be rejected
  as an argument while `RetentionConfig`'s own default stays untouched.
- Is there a documented upper bound for `/history`? No: `docs/23_agent/agent_07_07_*` documents only the
  default (`:40`) and no bound exists in code. The only bound stated anywhere in the repository is
  `/memory list`'s 1..200 (`memory_data_ops.py:86-88`), which this issue proposes to reuse.

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
