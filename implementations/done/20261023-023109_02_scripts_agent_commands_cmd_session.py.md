## Goal

Move the `/session` storage/maintenance/export/RAG group off the asyncio event loop so a
long `VACUUM`, `REBUILD`, or export cannot stall the REPL. Convert the `db_dispatch` table
in `cmd_session.py:_cmd_session` so every entry is a zero-argument callable returning an
awaitable (`asyncio.to_thread(...)`), and await it. This is the production half paired with
the regression test in row 04.

## Scope

Modify `scripts/agent/commands/cmd_session.py` only: add the `asyncio` import, rewrite the
`db_dispatch` table values to `asyncio.to_thread(...)` awaitables, widen the table's type
annotation, and `await` the handler. No sub-handler body, message text, or the
`list`/`load`/`rename`/`delete` branches change. No other file modified.

## Assumptions

- `_cmd_session` (`cmd_session.py:179`) is the awaited dispatcher for `/session`; the
  maintenance/export/RAG subcommands route through the `db_dispatch` table (`:215-232`) and
  are invoked at `:231` as `handler()` with no await.
- Every sub-handler is a synchronous method that opens and closes its own SQLite connection
  inside the call (`DbMaintenanceService`/`RagMaintenanceService`/`DbSessionOps` per
  invocation), so running it on a worker thread is safe (`check_same_thread=True`, REQ-004).
- `/session` already declares `is_async=True` (`command_defs_list.py:104`), so no metadata
  change is needed (REQ-007).
- The module imports `logging`, `Callable` (from `collections.abc`), and `Any` at `:14-16`;
  `asyncio` is not imported today.

## Design decisions

- **Wrap every entry in `asyncio.to_thread`** so the table has one value type
  `Callable[[], Awaitable[None]]` instead of mixing sync callables and lambdas. A mixed
  table would let a future subcommand silently block the loop again.
- **Offload the whole callable, not its DB part**, because the connection is created inside
  it (A2); splitting compute/thread vs print/loop would require restructuring five methods
  for no added safety (A3).
- **Keep `list`/`load`/`rename`/`delete` on the loop** (`:187-212`): they are outside the
  `db_dispatch` table and are the UNK-03 boundary; changing them is out of scope.
- **State the completion behavior accurately** (REQ-006): an offloaded call finishes even if
  its await is cancelled; interpreter shutdown joins the worker. Do not imply cancellation.

## Alternatives considered

- **Convert the service methods to `async def`.** Rejected: moves the concurrency decision
  into the storage services and requires signature changes across
  `db_maintenance_service.py`/`rag_maintenance_service.py`; the issue's Constraints forbid a
  DB-access-layer change beyond what offloading requires (REQ-007).
- **Use a dedicated executor (the `cli_view.py` pattern).** Rejected: commands are
  sequential (at most one worker in flight), so the loop's default executor suffices (A4);
  a dedicated pool is UNK-04, decided elsewhere.

## Implementation
### Target file
`scripts/agent/commands/cmd_session.py` (Modify)

### Procedure
1. Add `import asyncio` to the imports (`cmd_session.py:14-16`); also add `Awaitable` to the
   `typing` import (`:16`) for the new table type.
2. In `_cmd_session`, rewrite the `db_dispatch` table (`:215-228`) so every value is an
   `asyncio.to_thread(...)` awaitable:
   - Zero-arg bound methods: `"stats": asyncio.to_thread(self._db_session_stats),`.
   - Methods needing arguments: pass them positionally, e.g.
     `"checkpoint": asyncio.to_thread(self._db_session_ops.checkpoint, rest.strip().upper() or None),`.
   - Existing lambdas: replace `lambda: self._session_export(rest)` with
     `asyncio.to_thread(self._session_export, rest)` (and similarly for the others), so the
     argument is forwarded to the worker rather than captured in a closure called on the
     loop.
3. Widen the table annotation from `dict[str, Callable[[], None]]` to
   `dict[str, Callable[[], Awaitable[None]]]` (`:215`).
4. Change the invocation (`:231`) from `handler()` to `await handler()`.
5. Do not touch any sub-handler body, the success/validation message text, or the
   `list`/`load`/`rename`/`delete` branches (`:187-212`).

### Method
- Edit the import block, the table literal, the annotation, and the single call site. That
  is the entire change: four localized edits, no restructuring.
- Verify with `mypy --no-namespace-packages scripts/agent` that the typed `to_thread`
  table and `await handler()` type-check (`to_thread` returns `Coroutine[Any, Any, P]` /
  `Future`-like awaiting to the return type).
- Confirm the sub-handlers remain sync (they are called by the worker, not the loop).

### Details
- `asyncio.to_thread(func, *args)` runs `func(*args)` on the loop's default executor and
  returns an awaitable; the handler's return value flows back to `await handler()` (REQ-005:
  success output unchanged) and any exception (e.g. `sqlite3.Error`) propagates through to
  the caller (`:231`), so AC-4 exception behavior is preserved.
- Each entry must forward the SAME arguments the original lambda/method received, so
  behavior (and the `DbMaintenanceService` patch assertions in
  `tests/agent/commands/test_agent_cmd_session.py:509-600`) is unchanged (AC-4).
- `_cmd_session` stays C (13) complexity: the change adds no branch (validation baseline in
  the plan). Module size stays well under the 16384 B gate (one import + thirteen one-line
  wraps).
- `command_defs_list.py`, `db_session_ops.py`, `repl.py`, `repl_input_loop.py`,
  `signal_handler.py`, `db/helper.py` stay byte-identical (AC-7).

## Compatibility considerations

Output for successful runs is unchanged (same messages, order, `OutputPort` methods/tags,
REQ-005). Exceptions still propagate (AC-4). Process exit may be marginally slower because
`asyncio.run()` joins the default executor (a stated property, REQ-006; documented in
`agent_07_07`).

## Security considerations

No security impact: the change is a concurrency-boundary move, not an access or input
boundary. Worker-thread output ordering is covered by A3 (one command at a time).

## Rollback considerations

Revert the four edits in `scripts/agent/commands/cmd_session.py`: drop the `asyncio`
import, restore the original table values and annotation, and change `await handler()` back
to `handler()`. This restores the prior inline behavior exactly.

## Validation plan

1. `uv run pytest tests/agent/commands/test_command_blocking_offload.py -v` passes (AC-3,
   AC-5) against the offloaded code.
2. `uv run pytest tests/agent/commands/test_agent_cmd_session.py -v` passes unchanged,
   including the `purge(10, None)`-style argument asserts and the `vacuum` `sqlite3.Error`
   case (AC-4).
3. Regression: `uv run pytest tests/agent -q` and the metadata suites
   (`test_command_def_sync.py`, `test_command_defs.py`, `test_removed_commands.py`) pass
   unchanged; `git diff` shows no change to the AC-7 protected files (AC-7).
4. Static gates: `uv run ruff format scripts/agent`, `uv run ruff check scripts/agent`,
   `uv run mypy --no-namespace-packages scripts/agent`, `uv run vulture scripts/
   --min-confidence 80`, `uv run python tools/check_module_size.py`.

## Completion criteria

- The `db_dispatch` table is entirely `asyncio.to_thread(...)` awaitables; `_cmd_session`
  awaits them (REQ-003).
- Loop-responsiveness and completion-semantics tests pass (AC-3, AC-5).
- All existing `/session` tests pass unchanged, including `sqlite3.Error` cases (AC-4).
- Static gates clean; AC-7 protected files unchanged (AC-7).

## Out of Scope

- The `list`/`load`/`rename`/`delete` branches (`:187-212`, UNK-03).
- Converting the service methods to async, or any DB-layer change (REQ-007).
- Signal/shutdown wiring (`repl001`/`repl002`), which stays read-only.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261023-154041 | 20261023-154041 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261023-154041 | 20261023-154041 | offload regression test added in row 04; this cycle validated against existing test_agent_cmd_session.py + metadata suites |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261023-154041 | 20261023-154041 | full suite 9863 passed; ruff/mypy/lint-imports/bandit/vulture/clean; AC-7 files unchanged |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261023-154041 | 20261023-154041 | N/A: slash-commands-session doc update owned by row 06 (agent_07_07) |

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
- **Requirement ID**: REQ-003, REQ-005, REQ-006, REQ-007
- **Source issue**: issues/done/20261021-093421_cmd003-commands-block-the-event-loop-and-are-uncancellable.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261022-020701_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-023109
- **Related target files**: scripts/agent/commands/cmd_session.py