## Goal

Add `parse_int_arg` to `scripts/agent/commands/utils.py` as the single shared numeric
argument parser (REQ-001), and delete the dead helpers `parse_flag_int` (`:60-68`) and
`parse_flag_str` (`:71-76`) together with their `__all__` entries (`:18-19`) so no second
numeric parse path remains under `scripts/agent/commands/` (REQ-002; AC-8).

## Scope

In scope: one new function `parse_int_arg`, its import of `CommandValidationError`, and the
removal of `parse_flag_int`/`parse_flag_str`/their `__all__` entries in
`scripts/agent/commands/utils.py`. Out of scope: every call site that adopts the parser
(`cmd_context.py`, `cmd_session.py`, `db_session_ops.py`, `memory_data_ops.py`) — those are
separate rows.

## Assumptions

- **A5**: `parse_int_arg` stays free of any output/rendering responsibility — it raises, the
  call site renders. This keeps `utils.py` free of an `OutputPort` import and keeps `cmd001`'s
  `[usage]` mapping as the only path a raised `CommandValidationError` takes once it reaches
  `dispatch()`.
- The grammar to standardize on is `int()`-based (leading sign accepted, underscores per
  Python literal rules, non-ASCII digits rejected). Four of the five existing paths already
  use `int()`; `/memory list`'s `isdigit()` is the outlier this Plan aligns (UNK-01, UNK-02).

## Design decisions

- `parse_int_arg` raises the declared-but-unused `CommandValidationError`
  (`scripts/agent/commands/exceptions.py:13`, a `ValueError` subclass) instead of returning
  `None` or an error string. Returning `None` is exactly the defect — `_parse_optional_int`
  (`db_session_ops.py:11-16`) cannot tell "absent" from "invalid" — and an error-string field
  would repeat the unused `ParsedArgs.error` pattern (`utils.py:30`). `cmd001` already maps
  `CommandValidationError` to `[usage]`, so the raised type is the one the pipeline renders.
- Bounds (`minimum`/`maximum`) and the `usage` string are call-site keyword arguments, not
  fields of the parser. Each command passes its own bounds and usage text, so the rule exists
  once and every command renders its own message.

## Alternatives considered

- Returning `(value, ok)` or a sentinel: rejected as more ceremony than a raise, and the
  absent-vs-invalid distinction must survive end to end (a bare `--max-sessions` must still
  reach `_build_retention_config` as "absent", i.e. `None`, not as a parsed 0).
- Adding a range field to `ArgSpec`: rejected by the Plan (UNK-03) — it changes the
  declarative contract guarded by `tools/check_docs_consistency.py` and
  `tests/agent/commands/test_command_def_sync.py`, a larger change than this issue asks for.

## Implementation

### Target file

`scripts/agent/commands/utils.py`

### Procedure

Add `parse_int_arg` and delete the dead helpers in one step:

```python
def parse_int_arg(raw, *, usage, default=None, minimum=None, maximum=None) -> int | None:
    if raw is None:
        return default
    try:
        value = int(raw)
    except (ValueError, TypeError):
        raise CommandValidationError(usage) from None
    if minimum is not None and value < minimum:
        raise CommandValidationError(usage)
    if maximum is not None and value > maximum:
        raise CommandValidationError(usage)
    return value
```

Delete `parse_flag_int` (`:60-68`), `parse_flag_str` (`:71-76`), and their `__all__` entries
(`:18-19`). Import `CommandValidationError` at the top of the file.

### Method

Define the rule once; raise the declared-but-unused `CommandValidationError` (a `ValueError`
subclass) so `cmd001`'s `[usage]` mapping is the sole render path. No `OutputPort` import.

### Details

`ParsedArgs`/`parse_command_args` (`:23-57`) are unchanged. `raw is None` means "absent" → returns
`default`; a present-but-invalid value raises and never returns a default. `minimum`/`maximum` are
call-site keyword arguments, not parser fields.

## Compatibility considerations

- `parse_flag_int`/`parse_flag_str` are exported in `__all__` but have no call sites today
  (`grep -rn "parse_flag_int\|parse_flag_str" scripts tests` matches only their definitions
  and `__all__`). Removing them is safe; if any external caller exists it will surface as an
  `ImportError` in the full-suite run and must be migrated to `parse_int_arg`.

## Security considerations

- Rejecting `0`, negatives, and out-of-range values for `/session purge` prevents an operator
  misread from silently changing how much data a destructive command deletes
  (`--max-sessions 0` deletes everything, `--max-sessions -3` deletes the 3 oldest —
  `scripts/db/maintenance.py:185-202`). This is a correctness/integrity guard, not an
  authentication boundary.

## Rollback considerations

- The helper removal is a separate step from adding `parse_int_arg`; if needed, restore
  `parse_flag_int`/`parse_flag_str` and their `__all__` entries from `HEAD` before this row's
  commit, then re-run the suite.

## Validation plan

- `uv run pytest tests/agent/commands/test_command_arg_parsing.py -v` — all cases pass;
  `None` returned only for an absent argument (AC-1).
- `grep -rn "parse_flag_int\|parse_flag_str\|_parse_optional_int" scripts tests` returns no
  matches and `uv run vulture scripts/ --min-confidence 80` reports no new dead code (AC-8).
- `uv run ruff format scripts/agent` + `uv run ruff check scripts/agent`;
  `uv run mypy --no-namespace-packages scripts/agent`; `uv run python tools/check_module_size.py`.

## Completion criteria

- `parse_int_arg` exists with the exact signature in REQ-001, raises `CommandValidationError`
  for invalid/out-of-range input, returns `default` for `None`, and returns `None` only when
  `default` is itself `None`.
- `parse_flag_int`, `parse_flag_str`, and their `__all__` entries are gone; grep + vulture are
  clean (AC-8).

## Out of Scope

Every call site that adopts `parse_int_arg` (`cmd_context.py`, `cmd_session.py`,
`db_session_ops.py`, `memory_data_ops.py`) and the four test rows — each is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `parse_int_arg` to `scripts/agent/commands/utils.py` (raise `CommandValidationError`; no `OutputPort` import); keep `ParsedArgs`/`parse_command_args` unchanged | Completed | 2026-10-23 | 2026-10-23 | REQ-001, AC-1 |
| 2 | Delete `parse_flag_int`/`parse_flag_str` and their `__all__` entries; confirm AC-8 with grep + vulture | Completed | 2026-10-23 | 2026-10-23 | REQ-002, AC-8 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains (UNK-01..UNK-04 are non-blocking) | N/A: none | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `scripts/agent/commands/utils.py`
