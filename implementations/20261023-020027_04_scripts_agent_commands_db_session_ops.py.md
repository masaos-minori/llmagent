## Goal

Make `/session purge` validate `--max-sessions` (integer `>= 1`) and `--max-age-days`
(integer `>= 0`) through the shared numeric parser (`parse_int_arg`), skip the service call on
any invalid value, and delete the dead `_parse_optional_int` helper so no second numeric rule
set remains under `scripts/agent/commands/` (REQ-002, REQ-005; AC-4, AC-6, AC-8).

## Scope

In scope: `purge()` in `scripts/agent/commands/db_session_ops.py` (`:50-58`), the deletion of
`_parse_optional_int` (`:11-16`), and the rewrite of the two `…_treated_as_none` tests plus new
rejection cases in `tests/agent/commands/test_agent_cmd_session.py`. Out of scope: the retention
semantics in `scripts/db/maintenance.py` (unchanged) and the other three command rows.

## Assumptions

- `--max-sessions` gets `minimum=1` and `--max-age-days` gets `minimum=0` because the retention
  layer gives `0` a documented meaning only for the age flag (`maintenance.py:102`, `:169-170`);
  `--max-sessions 0` ("keep none") has no documented meaning and is rejected (A2).
- An absent flag must keep passing `None` so `RetentionConfig` defaults (100 / 90) still apply
  via `_build_retention_config` (`db_maintenance_service.py:87-96`). This is why "absent" and
  "invalid" must stay distinguishable — `parse_int_arg` returns `default` for absent and raises
  for invalid, whereas `_parse_optional_int` conflated them (A5).
- `test_purge_error_raises` (`:554-564`) requires `sqlite3.Error` to keep propagating, so only
  `CommandValidationError` may be caught at the call site; any other exception keeps propagating.

## Design decisions

- In `purge()`, replace `max_sessions = _parse_optional_int(parsed.flags.get("max-sessions"))`
  and the `--max-age-days` line with:
  ```python
  try:
      max_sessions = parse_int_arg(
          parsed.flags.get("max-sessions"), usage="/session purge …", minimum=1
      )
      max_age_days = parse_int_arg(
          parsed.flags.get("max-age-days"), usage="/session purge …", minimum=0
      )
  except CommandValidationError:
      self._out.write_validation_error("/session purge …")
      return
  result = DbMaintenanceService().purge(max_sessions, max_age_days)
  ```
  A bare `--max-sessions` arrives as `True`; `parse_int_arg(True, ...)` rejects it (not a valid
  integer), so the bare-flag case is covered by the same path as `0`/negative/non-integer.
- Delete `_parse_optional_int` entirely and add `from agent.commands.exceptions import (new)
  CommandValidationError` to `db_session_ops.py`. Confirm AC-8 with
  `grep -rn "parse_flag_int\|parse_flag_str\|_parse_optional_int" scripts tests` (no matches) and
  `uv run vulture scripts/ --min-confidence 80`.
- `parse_int_arg` stays free of output/rendering (A5); the call site renders.

## Alternatives considered

- Keeping `_parse_optional_int` and adding a separate range check: rejected — it leaves a second
  numeric rule set (the issue's core defect) and again cannot tell "absent" from "invalid".
- Bounds as `ArgSpec` fields: rejected by the Plan (UNK-03); bounds are call-site constants.

## Implementation

### Target file

`scripts/agent/commands/db_session_ops.py`

### Procedure

In `purge()` (`:50-58`), replace

```python
max_sessions = _parse_optional_int(parsed.flags.get("max-sessions"))
max_age_days = _parse_optional_int(parsed.flags.get("max-age-days"))
result = DbMaintenanceService().purge(max_sessions, max_age_days)
```

with

```python
try:
    max_sessions = parse_int_arg(
        parsed.flags.get("max-sessions"),
        usage="/session purge …",
        minimum=1,
    )
    max_age_days = parse_int_arg(
        parsed.flags.get("max-age-days"),
        usage="/session purge …",
        minimum=0,
    )
except CommandValidationError:
    self._out.write_validation_error("/session purge …")
    return
result = DbMaintenanceService().purge(max_sessions, max_age_days)
```

Then delete the module-level `_parse_optional_int` (`:11-16`) and import
`CommandValidationError`.

### Method

Validate both flags through the shared parser in one try; skip the service call on any rejection.
A bare flag arrives as `True`; `parse_int_arg(True, ...)` rejects it via the same path as `0`/
negative/non-integer. Absent flags stay `None` → retention defaults apply.

### Details

`--max-sessions` gets `minimum=1`; `--max-age-days` gets `minimum=0` (the retention layer gives
`0` a "disabled" meaning only for age — `maintenance.py:102`, `:169-170`). Only
`CommandValidationError` is caught, so `sqlite3.Error` still propagates
(`test_purge_error_raises`).

## Compatibility considerations

- `purge` with no flags still passes `(None, None)` (REQ-009, AC-4); `test_purge_success`
  (`:511-523`) is unchanged. `--max-sessions 10` still passes `(10, None)` and `--max-age-days 30`
  still passes `(None, 30)`; `test_purge_with_max_sessions` (`:526-537`) and
  `test_purge_with_max_age_days` (`:540-551`) are unchanged. `test_purge_error_raises` (`:554-564`)
  stays green because only `CommandValidationError` is caught.
- The two rewritten tests (`test_purge_with_non_numeric_max_sessions_treated_as_none` `:567`,
  `test_purge_with_non_numeric_max_age_days_treated_as_none` `:584`) currently assert
  `purge` is called with `None` — this Plan removes that behavior, so they become rejection tests
  asserting `purge` is not called.

## Security considerations

- Rejecting `--max-sessions 0` (delete everything), `--max-sessions -3` (delete the 3 oldest),
  and non-integers prevents an operator misread from silently changing how much data this
  destructive command deletes (`scripts/db/maintenance.py:185-202`). This is a correctness/
  integrity guard, not an authentication boundary.

## Rollback considerations

- The helper removal is a separate step from the `purge` change; if needed, restore
  `_parse_optional_int` from `HEAD` before this row's commit, then re-run the suite.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q` — purge rejection cases
  assert `purge` is not called; existing list/purge cases pass unchanged (AC-3, AC-4, AC-6).
- `grep -rn "parse_flag_int\|parse_flag_str\|_parse_optional_int" scripts tests` returns no
  matches; `uv run vulture scripts/ --min-confidence 80` reports no new dead code (AC-8).
- `uv run ruff format scripts/agent` + `uv run ruff check scripts/agent`;
  `uv run mypy --no-namespace-packages scripts/agent`.

## Completion criteria

- `purge()` validates both flags through `parse_int_arg` (`--max-sessions` `minimum=1`,
  `--max-age-days` `minimum=0`), skips the service call on rejection, and `--max-sessions 10` /
  `--max-age-days 30` / bare `purge` / `--max-age-days 0` still behave as today (AC-4, AC-9).
- `_parse_optional_int` is gone; grep + vulture are clean (AC-8).

## Out of Scope

Every other command that adopts `parse_int_arg` (`cmd_context.py`, `cmd_session.py`,
`memory_data_ops.py`) and their test rows — each is its own row. Retention semantics in
`scripts/db/maintenance.py` are unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the two `_parse_optional_int(...)` calls in `purge()` with `parse_int_arg` (`--max-sessions` minimum=1, `--max-age-days` minimum=0); skip the service call on rejection; delete `_parse_optional_int`; import `CommandValidationError` | Pending | — | — | REQ-002, REQ-005, REQ-007, REQ-009, AC-4, AC-6 |
| 2 | Rewrite the two `…_treated_as_none` tests as rejection tests asserting `purge` is not called; add bare-flag and negative-value purge cases; keep existing list/purge cases unchanged | Pending | — | — | REQ-004, REQ-005, REQ-009, AC-3, AC-4, AC-6 |
| 3 | Run the validation sequence (`rules/toolchain.md`), incl. grep + vulture for AC-8 | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-002`, `REQ-005`, `REQ-007`, `REQ-009`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `scripts/agent/commands/db_session_ops.py`
