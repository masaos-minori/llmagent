# Implementation: cmd_notes.py / cmd_session.py / cmd_memory.py — spec/parser migration

## Goal

Replace `if/elif` dispatch and ad-hoc arg parsing in three command files with
`parse_command_args()` based dispatch and `formatter.py` output.

## Scope

- `scripts/agent/commands/cmd_notes.py`
- `scripts/agent/commands/cmd_session.py`
- `scripts/agent/commands/cmd_memory.py`
- Tests: `tests/test_agent_cmd_notes.py`, `tests/test_agent_cmd_session.py`, `tests/test_agent_cmd_memory.py`

## Assumptions

1. The dispatch pattern changes from:
   ```python
   if sub == "add": ...
   elif sub == "list": ...
   ```
   to:
   ```python
   args = parse_command_args(tokens)
   dispatch = {"add": ..., "list": ...}
   handler = dispatch.get(args.subcommand)
   if handler is None:
       print_validation_error(f"Unknown subcommand: {args.subcommand!r}")
       return
   handler(args)
   ```
2. `arg.isdigit()` validation is replaced with `parse_command_args` + type check.
3. Direct `print()` calls are replaced with `formatter.*` calls.
4. state-changing operations (session rename/delete, memory pin/unpin/delete) remain
   calling the same underlying service methods — only the arg parsing and output change.
5. No new service classes are created in this step.

## Implementation

### cmd_notes.py procedure

1. Replace `args.strip().split()` with `parse_command_args(args.strip().split())`.
2. Replace `if sub == "add"` chain with dict dispatch.
3. Replace `arg.isdigit()` check in `_note_delete` with structured parsing.
4. Replace `print(...)` with `formatter.print_success / print_error / print_no_data / print_table`.

### cmd_session.py procedure

1. Replace `parts = args.strip().split()` + `if/elif` with `parse_command_args` + dict dispatch.
2. Replace `int(parts[1])` with `int(args.positional[0])` + ValueError → `print_validation_error`.
3. Replace direct `print(...)` with formatter calls.

### cmd_memory.py procedure

1. Replace `parts = args.strip().split(); sub = parts[0]` with `parse_command_args`.
2. Replace `dispatch = {...}` dict (currently stores lambdas) with subcommand handler dict
   that receives `ParsedArgs`.
3. Replace `print(...)` in each handler with formatter calls.

### Method

Direct textual edit for all three files.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/cmd_notes.py scripts/agent/commands/cmd_session.py scripts/agent/commands/cmd_memory.py` | 0 errors |
| Type | `uv run mypy scripts/agent/commands/cmd_notes.py scripts/agent/commands/cmd_session.py scripts/agent/commands/cmd_memory.py` | no new errors |
| Tests | `uv run pytest tests/test_agent_cmd_notes.py tests/test_agent_cmd_session.py tests/test_agent_cmd_memory.py -x -q` | all pass |
