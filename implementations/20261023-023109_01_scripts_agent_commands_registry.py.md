## Goal

Add a construction-time contract check to `CommandRegistry.__init__` so that a `CommandDef.is_async` value that disagrees with the actual kind of its handler (`inspect.iscoroutinefunction`) fails at startup as a `TypeError`, instead of surfacing only as a runtime `TypeError` when the command is later invoked.

## Scope

Modify `scripts/agent/commands/registry.py` only: extend the existing fail-fast handler-name validation loop in `__init__` with a handler-kind check, and add the `inspect` import. No other file is modified by this row. The production change is paired with a test added to `tests/agent/commands/test_command_registry_consistency.py` (row 03); that test file is not part of this row's modification target.

## Assumptions

- `is_async` is a required field of `CommandDef` (`command_defs.py:65`, no default), so all 14 registered entries already state it; the new check validates existing metadata rather than requiring new metadata.
- The 14 registered entries already satisfy the invariant (each `is_async=True` handler is a coroutine function and each `is_async=False` handler is sync), so the new check adds a startup failure surface but does not reject any currently-valid registry (AC-2).
- `inspect.iscoroutinefunction` correctly classifies bound methods of the registry (the handlers are bound methods exposed on the instance), which is why the check reads `getattr(self, cmd.handler)` rather than the unbound function.

## Design decisions

- **Extend the existing loop in `__init__`** rather than add a separate validation method: it is the only place all 14 `_COMMANDS` entries are enumerated before the registry is usable, and REQ-002 requires the new check to reuse the same lookup path as `_get_handler`.
- **Raise `TypeError`** (not a new exception class): it is the exception class the current invoke-time failure already produces (`'NoneType' object can't be awaited`), so the change moves the same failure earlier with an attributable message instead of introducing a new error surface (A1).
- **Import `inspect` locally in `registry.py`**: the module does not import `inspect` today (imports are at `:27-41`), so the import is part of this change.

## Alternatives considered

- **Validate in `_invoke_handler`**: rejected — that only fails at dispatch time, which is exactly the invisible-until-invoked defect REQ-001 removes.
- **Raise `ValueError` or a custom exception**: rejected — A1 records that `TypeError` keeps the failure class identical to today's invoke-time failure and avoids a new error-handling surface.
- **Check only `is_async=True` handlers**: rejected — REQ-001 requires the comparison both ways, so a wrongly-async sync handler is caught too.

## Implementation
### Target file
`scripts/agent/commands/registry.py`

### Procedure
1. Add `import inspect` to `registry.py` (module currently imports only `collections.abc.Callable` and `typing.Any` at `:27-28`).
2. In `CommandRegistry.__init__`, inside the existing fail-fast loop over `_COMMANDS` (currently `:68-72`, validating handler names via `hasattr`), add after the `hasattr` guard a handler-kind check: for each `_cmd`, look up the handler via the same path as `_get_handler` (`getattr(self, _cmd.handler)`), and if `inspect.iscoroutinefunction(handler)` does not equal `_cmd.is_async`, raise `TypeError` with a message naming the command name (`_cmd.name`), the handler name (`_cmd.handler`), and the mismatched kind.
3. Keep the existing `AttributeError` branch and its message byte-for-byte unchanged (REQ-002).
4. Do not modify `_invoke_handler` (`:105-113`): `is_async` keeps describing only how the dispatcher calls the handler.

### Method
Read `registry.py:27-41` (imports), `:62-81` (`__init__` + `_get_handler`), `:105-113` (`_invoke_handler`), and `command_defs.py:60-70` (`CommandDef.is_async` required field). Confirm `inspect` is absent from the imports and that the validation loop at `:68-72` validates only handler names. Then apply the two edits above (import + loop extension) and run the test in row 03 plus the unchanged consistency/dispatch/sync suites.

### Details
- Current `__init__` validation loop (`:67-72`):
  ```python
  # Fail-fast: validate all handler strings refer to existing methods.
  for _cmd in _COMMANDS:
      if not hasattr(self, _cmd.handler):
          raise AttributeError(
              f"CommandDef references unknown handler: {_cmd.handler!r}"
          )
  ```
- The new check reuses `_get_handler`'s lookup (`getattr(self, cmd.handler, None)`) so there is no second lookup path (REQ-002). Because `_get_handler` raises `AttributeError` for a missing handler, the `hasattr` guard must stay first; the kind check runs only for handlers that resolve.
- Suggested `TypeError` message shape (names all three required pieces):
  ```python
  handler = getattr(self, _cmd.handler)
  if inspect.iscoroutinefunction(handler) != _cmd.is_async:
      kind = "coroutine function" if inspect.iscoroutinefunction(handler) else "sync callable"
      raise TypeError(
          f"Command '{_cmd.name}' handler {_cmd.handler!r} is a {kind}, "
          f"but CommandDef.is_async={_cmd.is_async}"
      )
  ```
- Type note: `mypy --no-namespace-packages scripts/agent` must accept the `getattr` result used in `iscoroutinefunction`; the existing `_get_handler` already returns `Callable[..., Any]` with a `# type: ignore[no-any-return]`, so the same treatment is acceptable here.
- The check runs for every entry of `_COMMANDS` at construction, before the registry is usable (REQ-001), and no command is dispatched or handler invoked during it (AC-1).

## Compatibility considerations

- Output and dispatch behavior are unchanged for all valid registries (AC-2). `command_defs_list.py`, `db_session_ops.py`, `repl.py`, `repl_input_loop.py`, `signal_handler.py`, and `db/helper.py` are not touched (AC-7).
- The new startup failure only appears when a future entry sets `is_async` incorrectly; the 14 current entries already satisfy the invariant.

## Security considerations

None introduced. The check is a correctness contract, not an access or input-sanitization boundary.

## Rollback considerations

Reverting the two edits (import + loop extension) restores the prior behavior exactly; no schema, config, or deploy change accompanies this row.

## Validation plan

- Run the new construction-mismatch test (row 03) to confirm it raises `TypeError` with the command/handler names.
- Run the unchanged suites to confirm AC-2: `uv run pytest tests/agent/commands/test_command_registry_consistency.py tests/agent/commands/test_command_registry_dispatch.py tests/agent/commands/test_command_def_sync.py -v`.
- Static gates: `uv run ruff format scripts/agent` ; `uv run ruff check scripts/agent` ; `uv run mypy --no-namespace-packages scripts/agent` ; `uv run vulture scripts/ --min-confidence 80`.

## Completion criteria

- `CommandRegistry(...)` raised with a flipped `is_async` entry raises `TypeError` naming the command, handler, and kind (AC-1).
- `CommandRegistry(...)` constructs successfully with the 14 unchanged entries and the existing scans pass unchanged (AC-2).
- `git diff` shows no change to any file other than `scripts/agent/commands/registry.py` for this row.

## Out of Scope

- Any change to `_invoke_handler`, the dispatch path, or the `AttributeError` branch/message.
- Modifying `command_defs.py`, `command_defs_list.py`, or any test file (test is row 03).
- DB-layer interruptibility (`sqlite3.Connection.interrupt()`) — out of scope for the whole Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261023-151657 | 20261023-151657 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261023-151657 | 20261023-151657 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-151657 | 20261023-151657 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261023-151657 | 20261023-151657 | N/A: command-registry doc update owned by row 05 (agent_07_03) |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: `issues/done/20261021-093421_cmd003-commands-block-the-event-loop-and-are-uncancellable.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-020701_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-023109
- **Related target files**: `scripts/agent/commands/registry.py`