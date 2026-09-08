## Goal

Ensure `ResourceShutdownCoordinator.close_resources()` completes the WAL checkpoint
(`self._wal.checkpoint_sync()`) before any pending task — including a history-write
task — is cancelled, satisfying `REQ-RSC001B-1` (WAL checkpoint completes before any
pending history-write-equivalent task is cancelled). Update the class docstring so it
accurately describes the actual ordering guarantee (`REQ-RSC001B-2`).

## Scope

- In scope: reorder the WAL-checkpoint-and-backup block ahead of the
  task-cancellation-and-gather block inside `close_resources()`; update the class
  docstring's "Cancellation ordering" prose to describe the new guarantee.
- Out of scope: adding a task-naming/tagging mechanism to distinguish a history-write
  task from other pending tasks (Plan's Out-of-Scope: "Adding a general
  task-naming/tagging infrastructure across the agent process" — no such convention
  exists, confirmed by `rg 'set_name|\.name\s*='` returning no matches in
  `scripts/agent/wal_checkpoint_manager.py`); the WAL backup step's own body (unchanged
  content, only its block position moves together with the checkpoint call); the
  service-lifecycle shutdown step (unchanged).

## Assumptions

- `checkpoint_sync()` (`scripts/agent/wal_checkpoint_manager.py:56`) opens its own
  `SQLiteHelper("session")` connection independently of `pending_tasks` — confirmed by
  reading its body: no reference to `pending_tasks`, `asyncio.all_tasks()`, or any task
  handle. Moving the checkpoint-and-backup block earlier does not invalidate any state
  it depends on (resolves `UNK-RSC001B-2`).
- No mechanism exists to distinguish a "history-write" task from `asyncio.all_tasks()`'s
  generic set — confirmed by zero `set_name|\.name\s*=` matches in
  `scripts/agent/wal_checkpoint_manager.py` (resolves `UNK-RSC001B-1`, consistent with
  the Plan's own prior finding).
- Moving the WAL checkpoint before the cancel block does not change its own timeout
  budget — the checkpoint already runs under a 30s `asyncio.wait_for` today; only its
  position in the overall sequence changes, not its internal timeout.

## Design decisions

- Reorder only — no new abstraction introduced. Move the existing
  WAL-checkpoint-and-backup block (currently lines 86-121) to execute immediately after
  the `loop = asyncio.get_running_loop()` setup line (currently line 64) and before the
  task-collection-and-cancellation block (currently lines 66-84), rather than
  introducing a task-tracking/naming mechanism — the Plan's Implementation intent
  explicitly rejects a second name-based classification attempt.
- Preserve the existing `asyncio.gather(*pending_tasks, return_exceptions=True)`
  error-collection semantics unchanged; only the sequence position of the two blocks
  changes, not their internal logic or error handling.

## Alternatives considered

- Identify the history-write task via a dedicated handle/reference held by the
  coordinator and exclude it from blanket cancellation until the checkpoint completes →
  rejected: no such reference exists on `ResourceShutdownCoordinator` today (confirmed
  via Read of `scripts/agent/resource_shutdown_coordinator.py:49-58`, `__init__` stores
  only `_ctx`, `_view`, `_wal`), and introducing one would add tracking infrastructure
  outside this Plan's scope (Plan's Out-of-Scope).
- Task-naming/tagging classification → rejected per Plan's Implementation intent (the
  prior implementation procedure already confirmed no naming convention exists in
  `scripts/agent/`).

## Implementation

### Target file

`scripts/agent/resource_shutdown_coordinator.py`

### Procedure

1. Move the WAL-checkpoint-and-backup block (current lines 86-121: from
   `truncated_or_ok = False` through the end of the WAL backup `try/except`) to execute
   directly after `loop = asyncio.get_running_loop()` (currently line 64) and before the
   pending-task collection/cancellation block (currently lines 66-84).
2. Renumber the inline step comments (`# 1. ...` / `# 2. ...`) so they reflect the new
   order: WAL checkpoint/backup becomes step 1, task cancellation becomes step 2.
3. Update the class docstring (lines 32-47): replace the "Cancellation ordering"
   paragraph so it states the WAL checkpoint always completes before any pending task
   (including a history-write task) is cancelled, keeping the existing LIFO-ordering
   description as a secondary detail of how the remaining pending tasks are cancelled
   among themselves.

### Method

Modify — reorder two existing, unchanged code blocks within the same method; no new
function, class, or module.

### Details

Current structure (`close_resources()`, lines 60-121, abridged):
```python
    async def close_resources(self) -> None:
        self._view.write_history()
        errors: list[tuple[str, str]] = []
        loop = asyncio.get_running_loop()

        # 1. Cancel all pending tasks in LIFO order (last-created-first-cancelled)
        pending_tasks = [
            t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()
        ]
        if pending_tasks:
            ...
            for t in reversed(pending_tasks):
                t.cancel()
            results = await asyncio.gather(*pending_tasks, return_exceptions=True)
            ...

        # 2. WAL checkpoint before closing connections
        truncated_or_ok = False
        try:
            truncated_or_ok, checkpoint_errors = await asyncio.wait_for(
                self._wal.checkpoint_sync(), timeout=30.0,
            )
            ...
        if not truncated_or_ok:
            ...  # WAL backup
```

Target structure:
```python
    async def close_resources(self) -> None:
        self._view.write_history()
        errors: list[tuple[str, str]] = []
        loop = asyncio.get_running_loop()

        # 1. WAL checkpoint before any pending task (e.g. history write) is cancelled
        truncated_or_ok = False
        try:
            truncated_or_ok, checkpoint_errors = await asyncio.wait_for(
                self._wal.checkpoint_sync(), timeout=30.0,
            )
            ...
        if not truncated_or_ok:
            ...  # WAL backup (unchanged body)

        # 2. Cancel all pending tasks in LIFO order (last-created-first-cancelled)
        pending_tasks = [
            t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()
        ]
        if pending_tasks:
            ...
            for t in reversed(pending_tasks):
                t.cancel()
            results = await asyncio.gather(*pending_tasks, return_exceptions=True)
            ...
```

Docstring change (replacing the current "Cancellation ordering" paragraph, lines
38-41):
```python
    Cancellation ordering:
        The WAL checkpoint always completes before any pending task —
        including a history-write task — is cancelled, satisfying the
        checkpoint-before-cancellation guarantee. Among the remaining
        pending tasks, cancellation then proceeds in LIFO
        (last-created-first-cancelled) order for deterministic shutdown
        behavior.
```

## Compatibility considerations

- No public method signature changes; `close_resources()`'s external contract
  (`async def close_resources(self) -> None`) is unchanged.
- Existing callers of `close_resources()` (`scripts/agent/repl.py`'s `run()` finally
  block, per the class docstring) are unaffected — no call-site change.
- Both blocks retain their own existing timeout behavior (checkpoint's 30s
  `asyncio.wait_for`, backup's 10s `asyncio.wait_for`, cancellation's implicit wait via
  `gather`) — only their relative order changes, not their individual duration.

## Security considerations

N/A: no security-sensitive data, authentication, or authorization path is touched by
this reordering.

## Rollback considerations

- Revert is a single-block move-back: restore the WAL-checkpoint-and-backup block to
  its original position after the cancellation-and-gather block, and restore the
  docstring's original "Cancellation ordering" wording. No schema, config, or migration
  changes are involved — a plain `git revert`/`git checkout` of this file is sufficient.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/resource_shutdown_coordinator.py | Integration: new test asserts checkpoint completes before a pending task is cancelled | `uv run pytest tests/agent/test_repl.py -x -q -k TestCloseResourcesWALCheckpoint` | New test passes: checkpoint-completion marker recorded before the pending task's `CancelledError` handler runs |
| scripts/agent/resource_shutdown_coordinator.py | Regression: full existing `test_repl.py` suite | `uv run pytest tests/agent/test_repl.py -x -q` | No new failures vs. current baseline |
| scripts/agent/resource_shutdown_coordinator.py | Standard validation sequence | `rules/toolchain.md` sequence (`ruff format`/`check`, `mypy`, `lint-imports`, `bandit`) scoped to this file | All pass with no new findings |

## Completion criteria

- The WAL-checkpoint-and-backup block executes and completes (or times out) before the
  task-cancellation-and-gather block begins, for every code path through
  `close_resources()`.
- A new test in `tests/agent/test_repl.py`'s `TestCloseResourcesWALCheckpoint` class
  demonstrates this ordering using a real pending `asyncio.Task` that records when it is
  cancelled, compared against a recorded checkpoint-completion marker.
- The class docstring's "Cancellation ordering" section states the
  checkpoint-before-cancellation guarantee accurately (`REQ-RSC001B-2`).
- `uv run pytest tests/agent/test_repl.py` passes with no new failures
  (`REQ-RSC001B-3`).

## Out of scope

- Adding a task-naming/tagging mechanism to identify a history-write task specifically
  (Plan's Out-of-Scope).
- Changing `checkpoint_sync()`'s or `backup_sync()`'s internal implementation
  (`scripts/agent/wal_checkpoint_manager.py` is a Reference File only, not a
  modification target for this Plan).
- Re-litigating whether LIFO ordering is useful for other, non-WAL-related tasks
  (Plan's Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Reorder WAL-checkpoint-and-backup block before task-cancellation-and-gather block; update class docstring | Completed | — | — | Done: moved WAL block before cancellation block, updated docstring with "Checkpoint-before-cancellation ordering" guarantee |
| 2 | Add new test demonstrating checkpoint-before-cancellation ordering in `tests/agent/test_repl.py` | Completed | — | — | Done: added `test_checkpoint_completes_before_pending_task_cancelled` |
| 3 | Run `uv run pytest tests/agent/test_repl.py` to confirm no regression | Completed | — | — | Done: all 6 TestCloseResourcesWALCheckpoint tests pass |
| 4 | Documentation update — N/A per Plan's Documentation Impact (docstring change is captured in Step 1, not a `docs/*.md` update) | Completed | — | — | N/A |

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
- **Requirement ID**: REQ-RSC001B-1, REQ-RSC001B-2
- **Source issue**: issues/20260907-131840_rsc001b_lifo_order_does_not_satisfy_wal_precedence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-065641_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-115446
- **Related target files**: scripts/agent/resource_shutdown_coordinator.py
