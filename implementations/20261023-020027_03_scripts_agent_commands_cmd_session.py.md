## Goal

Make `/session list [n]` validate its positional argument through the shared numeric parser
(`parse_int_arg`) so a non-integer, `0`, a negative value, or a value above `200` produces a
usage error and calls `Session.list_sessions` zero times, while an omitted `n` keeps the current
default of 20 (REQ-004; AC-3, AC-6).

## Scope

In scope: `_session_list` in `scripts/agent/commands/cmd_session.py` (`:77-88`) and its
rejection cases in `tests/agent/commands/test_agent_cmd_session.py`. Out of scope: every other
command that adopts `parse_int_arg` — those are separate rows.

## Assumptions

- The upper bound `200` is the intended reference bound (A3); UNK-01 records the alternative.
- `_session_list` receives the raw CLI positional directly (its parameter is `limit_arg: str`),
  and empty string means "omitted" — so `parse_int_arg(default=20)` treats `""` as absent → 20.
- The sibling `_parse_positive_session_id` (`cmd_session.py:43-54`) already uses the
  reject-and-report pattern, so this row follows the established convention.

## Design decisions

- Replace the `try: limit = int(limit_arg) if limit_arg else 20 except (ValueError, TypeError): limit = 20`
  block with `parse_int_arg(usage="/session list [n]", default=20, minimum=1, maximum=200)`
  wrapped in `try/except CommandValidationError`. On rejection, return before calling
  `list_sessions`, so it is called zero times (AC-3). The call site renders the command's own
  usage string via `write_validation_error`.
- `parse_int_arg` stays free of output/rendering (A5); no `OutputPort` import is added here by
  this row.

## Alternatives considered

- Keeping the silent `except: limit = 20` fallback: rejected — it is exactly the defect (a bare
  `/session list abc` becomes 20 with no message).
- Bounds as `ArgSpec` fields: rejected by the Plan (UNK-03); bounds are call-site constants.

## Implementation

### Target file

`scripts/agent/commands/cmd_session.py`

### Procedure

In `_session_list` (`:77-88`), replace

```python
try:
    limit = int(limit_arg) if limit_arg else 20
except (ValueError, TypeError):
    limit = 20
raw_rows = self._ctx.session.list_sessions(limit)
```

with

```python
try:
    limit = parse_int_arg(
        limit_arg, usage="/session list [n]", default=20, minimum=1, maximum=200
    )
except CommandValidationError:
    self._out.write_validation_error("/session list [n]")
    return
raw_rows = self._ctx.session.list_sessions(limit)
```

Import `CommandValidationError`.

### Method

Replace the silent `except: limit = 20` fallback with the shared parser; return before
`list_sessions` on rejection so it is called zero times. Mirrors the reject-and-report pattern of
the sibling `_parse_positive_session_id` (`:43-54`).

### Details

An empty `limit_arg` (omitted) is treated as absent → default 20. A non-integer, `0`, negative, or
`>200` raises and renders the usage error without calling `list_sessions`.

## Compatibility considerations

- `/session list` with no argument still calls `list_sessions(20)` (REQ-009, AC-3);
  `test_list_default_limit_is_20` (`:88-91`) and `test_list_custom_limit` (`:94-97`) are
  unchanged. An uncaught `CommandValidationError` would surface in these direct-call tests
  instead of a usage line (A4), so the catch must be present.

## Security considerations

- Rejecting a negative limit prevents it reaching `list_sessions`'s `LIMIT ?` as a SQL-level
  behavior (`scripts/agent/session.py:175-185`), where it would select the wrong rows. This is a
  correctness/integrity guard, not an authentication boundary.

## Rollback considerations

- The change is a single-function swap; revert `cmd_session.py` to `HEAD` for this row's commit
  if needed, then re-run the suite.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q` — new `/session list`
  rejection cases assert `list_sessions` is not called; existing list cases pass unchanged
  (AC-3).
- `uv run ruff format scripts/agent` + `uv run ruff check scripts/agent`;
  `uv run mypy --no-namespace-packages scripts/agent`.

## Completion criteria

- `_session_list` calls `parse_int_arg(usage="/session list [n]", default=20, minimum=1, maximum=200)`
  and returns without calling `list_sessions` on rejection (AC-3).
- `/session list abc`, `/session list 0`, `/session list -1` produce the usage error and do not
  call `list_sessions`; `/session list` with no argument still calls it with 20, `/session list 5`
  still with 5 (AC-3, AC-9).

## Out of Scope

Every other command that adopts `parse_int_arg` (`cmd_context.py`, `db_session_ops.py`,
`memory_data_ops.py`) and their test rows — each is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the `try: int(limit_arg) … except: limit = 20` block in `_session_list` with `parse_int_arg(usage="/session list [n]", default=20, minimum=1, maximum=200)`; return before `list_sessions` on rejection | Pending | — | — | REQ-004, REQ-007, REQ-009, AC-3, AC-6 |
| 2 | Add `/session list abc`, `/session list 0`, `/session list -1` rejection cases to `tests/agent/commands/test_agent_cmd_session.py`; keep existing list cases unchanged | Pending | — | — | REQ-004, REQ-009, AC-3, AC-6 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004`, `REQ-007`, `REQ-009`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `scripts/agent/commands/cmd_session.py`
