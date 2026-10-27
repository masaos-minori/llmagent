## Goal

Offload the `TurnPersistence` sync sqlite calls onto worker threads with
`await asyncio.to_thread(...)` so the event loop never executes session-DB writes
during a turn (REQ-001), while sequential awaits preserve strict within-turn write
ordering (REQ-003) and the public awaitable signatures stay unchanged (REQ-004).

## Scope

- Only `scripts/agent/turn_persistence.py`:
  - `save` (async, L82-93), `save_many` (L95-103), `save_phase_grouped` (L105-118),
    `replace_messages` (L120-130): wrap the sync
    `self.session._message_repo.<method>(...)` call in
    `await asyncio.to_thread(...)`.
  - `_compensate` (sync, L132-138): its
    `self.session._message_repo.delete_messages_from(...)` call is moved into an
    `asyncio.to_thread` call awaited from `_fail_from_error` (async, L140+);
    `_compensate` may become `async def` (new shape) — either variant is acceptable as
    long as the delete executes on a worker thread.
  - Add `import asyncio`; update the module docstring to record that every turn write
    (and the compensation delete) runs on a worker thread via `asyncio.to_thread`.
- No signature changes: all phase methods stay `async def` with the same parameters
  and return types.

## Assumptions

- Current shipped state (verified Step 2): the phase methods are already `async def`
  (turn001 shipped) but call the sync repository on the loop thread; this row's delta
  is exactly the `to_thread` offload, not the async conversion.
- Shipped-vs-plan discrepancy: the frozen row says "boundary connection opened with
  `check_same_thread=False`", but the shipped boundary holds no connection — each
  repository call opens/closes its own connection inside the sync method, which after
  this change is created and used entirely on one worker thread (safe under the sqlite3
  default `check_same_thread=True`; the Plan's Background states this explicitly for
  the per-call pattern). The `check_same_thread` knob from
  `implementations/20261028-003125_01_scripts_db_helper.py.md` is therefore not wired
  in this file today; it becomes required only if a later refactor hands the boundary a
  reused connection (`SQLiteHelper.open(check_same_thread=False)`). Record this in the
  implementation notes.
- `_fail_from_error`'s memory-restore and error-wrapping stay on the loop thread
  (pure in-memory work); only the DB delete moves to a worker thread.
- Ordering (REQ-003) is preserved because call sites already `await` each phase
  sequentially (verified: `llm_turn_runner.py`, `conversation_state_manager.py`,
  `tool_round_completion.py`, `workflow_engine_adapter.py` all await the boundary).
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this file; this file's turn001 procedures
  (`implementations/done/20261027-094147_01_*`) cover the async-conversion portion
  already implemented — this document covers only the offload remainder.

## Design decisions

- Offload inside the boundary (single wrapper) rather than in `SessionMessageRepository`
  or at call sites — issue Constraint: one persistence wrapper only (REQ-001).
- Keep the `try/except sqlite3.Error` around the awaited `to_thread` call: the
  exception propagates out of the worker thread through the await and into the existing
  compensation path unchanged.

## Alternatives considered

- Give `TurnPersistence` its own reused connection (turn001 Plan Design as written):
  rejected for this step — the shipped repository API does not accept an injected
  connection for `save`/`save_many`, and switching connection models now would change
  turn001's shipped transaction behavior beyond this row's scope. Revisit only with an
  explicit Plan update; the REQ-002 knob already makes it legal when needed.
- `run_in_executor` with a dedicated single-thread executor: rejected — `to_thread` is
  the established pattern in this repo (`cmd_session.py` L222-228 dispatch table,
  `wal_checkpoint_manager.py`) and preserves ordering via sequential awaits without
  an extra executor to manage.

## Implementation

### Target file

`scripts/agent/turn_persistence.py`

### Procedure

Wrap each sync repository call in `await asyncio.to_thread(...)`; leave control flow,
error semantics, and signatures identical.

### Method

1. Add `import asyncio` to the import block (after `import logging`).
2. `save`: `await asyncio.to_thread(self.session._message_repo.save, role, content, tool_calls, tool_call_id)`.
3. `save_many`: `await asyncio.to_thread(self.session._message_repo.save_many, messages)`.
4. `save_phase_grouped`: `await asyncio.to_thread(self.session._message_repo.save_phase_grouped, messages)`.
5. `replace_messages`: `return await asyncio.to_thread(self.session._message_repo.replace_messages, self.session_id, messages)` (keep the `session_id is None` early return and the unreachable-after-`_fail_from_error` `return None`).
6. `_compensate` → `async def _compensate`, with
   `return await asyncio.to_thread(self.session._message_repo.delete_messages_from, self.session_id, self.turn_start_message_id)`;
   update `_fail_from_error` to `await self._compensate()`.
7. Update the module docstring (Write routing paragraph) to state that each phase call
   runs on a worker thread via `asyncio.to_thread`, with the repository's
   `begin_immediate` grouping unchanged.

### Details

- `asyncio.to_thread` passes positionally; all repository arguments are plain values
  already owned by the caller (message tuples, ids) — no shared mutable state crosses
  the thread boundary except `self.session._message_repo` itself, whose stats counters
  (`stat_skipped_*`) are incremented from whichever thread runs the call; verify no test
  asserts counter thread-identity (none found today).
- `ConversationPersistenceError` chaining (`raise ... from exc`) stays inside
  `_fail_from_error`; `sqlite3.Error` raised in the worker thread re-raises unchanged
  at the await site, so `exc.__cause__` semantics are preserved.

## Compatibility considerations

- Public API unchanged: consumers already `await boundary.save*` /
  `await boundary.replace_messages` — no call-site edits are required by this document
  (rows 03-07 cover the already-shipped await state).
- Implement only after `..._01_...` (helper knob) and `..._08_...` (probe test) per the
  Plan's phase order (P2 before P3); REQ-005 probe evidence gates the offload.

## Security considerations

- No new I/O or config surface. Worker threads are the stdlib default executor;
  connections are per-call and thread-local (no cross-thread connection sharing).

## Rollback considerations

- Reverting this single file restores loop-thread writes with identical semantics
  (turn001 behavior). Keep it as its own commit so a regression bisect can isolate the
  offload from the helper change.

## Validation plan

- Extended tests in `tests/agent/test_turn_persistence.py`
  (`implementations/20261028-003125_09_tests_agent_test_turn_persistence.py.md`):
  off-loop-thread execution proof and the locked-write contention test (REQ-006).
- Regression: `uv run pytest tests/agent/test_turn_persistence.py tests/agent/test_orchestrator.py`
  then the full validation sequence (`rules/toolchain.md`).

## Completion criteria

- A phase write is proven to run on a thread other than the event loop's thread while
  the loop stays responsive (REQ-001, REQ-006 acceptance).
- All existing turn-persistence and turn-flow tests green without signature changes
  (REQ-004).

## Out of Scope

- Changing `SessionMessageRepository` to accept an injected/reused connection.
- Command-path writes (`cmd_session.py` dispatch table) — already offloaded.
- `tool_runner.py` L430 `ctx.session.save_many([])` — verified no-op (opens no
  connection); untouched per Plan Scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| 20261028-003125-02 | 2 | test | Planned | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: `issues/20261026-225134_sess008_offload-session-sqlite-writes.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-090510_sess008_offload-session-sqlite-writes.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-003125
- **Related target files**: `scripts/agent/turn_persistence.py`
