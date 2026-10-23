## Goal

Make `/history [n]` validate its positional argument through the shared numeric parser
(`parse_int_arg`) so `0`, negatives, and values above `200` are reported as usage errors and
print nothing, while an omitted `n` keeps the current default of 5 (REQ-003; AC-2, AC-6).

## Scope

In scope: `_cmd_history` in `scripts/agent/commands/cmd_context.py` (`:138-149`) and its
rejection cases in `tests/agent/commands/test_agent_cmd_context.py`. Out of scope: every other
command that adopts `parse_int_arg` — those are separate rows.

## Assumptions

- The upper bound `200` is the intended reference bound (A3): `/memory list`'s 1..200 is the
  only existing display-size bound and is documented (`agent_07_10:39`). UNK-01 records the
  alternative (reject non-positive only, no upper bound); if the owner prefers that, only the
  `maximum=` constant and the doc wording change.
- `parse_command_args` already returns the raw token via `parsed.subcommand or "5"` at
  `cmd_context.py:141`, so an omitted argument reaches `parse_int_arg` as `None` (absent →
  default 5).

## Design decisions

- Replace the `try: n = int(raw) except ValueError: write_validation_error` block with a single
  `parse_int_arg(usage="/history [n]", default=5, minimum=1, maximum=200)` call wrapped in
  `try/except CommandValidationError`. The parser raises for invalid/out-of-range input; the
  call site renders the command's own usage string. This matches the reject-and-report pattern
  the sibling `_parse_positive_session_id` (`cmd_session.py:43-54`) already uses.
- `parse_int_arg` stays free of output/rendering (A5): it raises, the call site renders. No
  `OutputPort` import is added to `utils.py` by this row.

## Alternatives considered

- Keeping the local `int()` + `except ValueError`: rejected because it leaves a second numeric
  rule set (the issue's core defect) and would still accept `0`/negatives/`>200`.
- Adding an upper bound via `ArgSpec`: rejected by the Plan (UNK-03); bounds are call-site
  constants, not declarative `ArgSpec` fields.

## Implementation

### Target file

`scripts/agent/commands/cmd_context.py`

### Procedure

In `_cmd_history` (`:138-149`), replace

```python
raw = parsed.subcommand or "5"
try:
    n = int(raw)
except ValueError:
    self._out.write_validation_error("/history [n]")
    return
```

with

```python
try:
    n = parse_int_arg(
        parsed.subcommand or "5",
        usage="/history [n]",
        default=5,
        minimum=1,
        maximum=200,
    )
except CommandValidationError:
    self._out.write_validation_error("/history [n]")
    return
```

Import `CommandValidationError`.

### Method

Raise at the parser, render at the call site via the existing `write_validation_error`. An omitted
`n` reaches the parser as `None` (absent) → default 5.

### Details

On rejection the handler returns before `turns[-n:]` (`:149`), so nothing is printed. The default
of 5 is preserved because `parse_int_arg(..., default=5)` returns 5 for the absent argument.

## Compatibility considerations

- `/history` with no argument still prints the last 5 messages (REQ-009, AC-2); the existing
  `test_history_default_is_5` case is unchanged. The existing `test_history_invalid_n_shows_usage`
  (`:496-501`) asserts on the tag text ("usage"), not the message body, so it stays green once
  the parser raises `CommandValidationError` and the call site renders via
  `write_validation_error`.

## Security considerations

- Rejecting `0`/negatives/`>200` prevents an operator misread from printing the entire history
  (`turns[-0:]`) or the oldest messages (`turns[-3:]`) instead of a bounded preview. This is a
  correctness guard, not an authentication boundary.

## Rollback considerations

- The change is a single-function swap; revert `cmd_context.py` to `HEAD` for this row's commit
  if needed, then re-run the suite.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_cmd_context.py -q` — new rejection cases pass;
  existing `TestCmdHistory` cases pass unchanged (AC-2).
- `uv run ruff format scripts/agent` + `uv run ruff check scripts/agent`;
  `uv run mypy --no-namespace-packages scripts/agent`.

## Completion criteria

- `_cmd_history` calls `parse_int_arg(usage="/history [n]", default=5, minimum=1, maximum=200)`
  and prints nothing on rejection (AC-2).
- `/history 0`, `/history -3`, `/history 201` produce the usage error and print nothing;
  `/history` with no argument still prints the last 5 (AC-2, AC-9).

## Out of Scope

Every other command that adopts `parse_int_arg` (`cmd_session.py`, `db_session_ops.py`,
`memory_data_ops.py`) and their test rows — each is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `int()`/`except ValueError` block in `_cmd_history` with `parse_int_arg(usage="/history [n]", default=5, minimum=1, maximum=200)`; print nothing on rejection | Completed | 2026-10-23 | 2026-10-23 | REQ-003, REQ-007, REQ-009, AC-2, AC-6 |
| 2 | Add `/history 0`, `/history -3`, `/history 201` rejection cases to `tests/agent/commands/test_agent_cmd_context.py`; keep existing cases unchanged | Completed | 2026-10-23 | 2026-10-23 | REQ-003, REQ-009, AC-2, AC-6 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-23 | 2026-10-23 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-23 | 2026-10-23 | — |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains (UNK-01's bounds are two call-site constants) | N/A: none | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003`, `REQ-007`, `REQ-009`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `scripts/agent/commands/cmd_context.py`
