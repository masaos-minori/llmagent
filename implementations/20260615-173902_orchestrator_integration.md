# Implementation: scripts/agent/orchestrator.py — WorkflowEngine Integration

## Goal

Wire `WorkflowEngine` into `Orchestrator.handle_turn()` with minimal changes: wrap the existing plan / execute / verify handlers as async callbacks, create a `TaskRecord` per turn, and run the engine. Existing turn logic must not be modified.

## Scope

**In:**
- `scripts/agent/orchestrator.py` — add WorkflowEngine wiring inside `handle_turn()`

**Out:**
- Changes to `LLMTurnRunner`, `ToolLoopGuard`, or any other module
- UI or CLI output changes
- New public methods on `Orchestrator`

## Assumptions

1. `WorkflowEngine` wraps the existing turn phases as callbacks; the inner logic is unchanged.
2. `session_id` is available on `self._ctx` as `ctx.session_id` (string).
3. `turn_number` is available as `ctx.turn_counter` (int) or equivalent.
4. `StateStore` is instantiated per `handle_turn()` call and closed in a `finally` block.
5. `WorkflowDef` is loaded once at `Orchestrator.__init__` time via `WorkflowLoader().load()`.
6. The `WorkflowEngine` integration is purely additive — if `WorkflowEngine` raises `WorkflowHaltError` or `WorkflowTimeoutError`, the error propagates through the existing error handler (`self._on_error`).
7. `idempotency_key = f"{ctx.session_id}:{ctx.turn_counter}"` — unique per session turn.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. Add imports for `WorkflowEngine`, `WorkflowLoader`, `StateStore`, `WorkflowHaltError`.
2. In `__init__`: load `WorkflowDef` once via `WorkflowLoader().load()`.
3. In `handle_turn()`: create `StateStore`, create `TaskRecord`, run `WorkflowEngine.run()`.

### Method

#### New imports (add after existing imports)

```python
from agent.workflow.models import WorkflowDef
from agent.workflow.state_store import StateStore
from agent.workflow.workflow_engine import WorkflowEngine, WorkflowHaltError
from agent.workflow.workflow_loader import WorkflowLoader
```

#### `__init__` addition

After `self._llm_runner = LLMTurnRunner(...)`, add:
```python
try:
    self._workflow_def: WorkflowDef = WorkflowLoader().load()
except Exception:
    logger.warning("WorkflowLoader failed — workflow tracking disabled")
    self._workflow_def = None  # type: ignore[assignment]
```

#### `handle_turn()` replacement

Replace the body of `handle_turn` to wrap the existing call in workflow tracking:

```python
async def handle_turn(self, line: str) -> None:
    """Call LLM with the user message and persist to DB."""
    ctx = self._ctx
    turn_started_at = time.perf_counter()

    if self._workflow_def is None:
        # Workflow tracking disabled — fall back to original flow
        await self._handle_turn_start(line)
        answer, error_kind = await self._process_turn(line, ctx, turn_started_at)
        await self._handle_turn_end(line, answer, turn_started_at, error_kind)
        return

    store = StateStore()
    try:
        session_id = str(ctx.session_id) if ctx.session_id else str(uuid.uuid4())
        turn_number = int(getattr(ctx, "turn_counter", 0))
        task = store.create_task(
            session_id=session_id,
            turn_number=turn_number,
            workflow_version=self._workflow_def.version,
        )
        engine = WorkflowEngine(self._workflow_def, store)

        async def plan_fn() -> None:
            await self._handle_turn_start(line)

        async def execute_fn() -> None:
            nonlocal answer, error_kind
            answer, error_kind = await self._process_turn(line, ctx, turn_started_at)

        async def verify_fn() -> None:
            await self._handle_turn_end(line, answer, turn_started_at, error_kind)

        answer: str = ""
        error_kind: str | None = None
        await engine.run(task, plan_fn, execute_fn, verify_fn)
    except WorkflowHaltError as exc:
        logger.error("Turn halted by workflow engine: %s", exc)
        if self._on_error:
            self._on_error(exc)
    finally:
        store.close()
```

### Details

- `answer` and `error_kind` are captured by the closures via `nonlocal` — this is the minimal-change pattern that avoids refactoring `_process_turn`.
- `WorkflowDef` loaded at `__init__` time is shared across all turns; it is read-only.
- `StateStore` is created and closed per turn to avoid connection leaks.
- The `_workflow_def is None` guard ensures the original flow works even if the workflow file is missing (graceful degradation).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Existing tests | `uv run pytest tests/test_orchestrator.py -v` | all pass (no regression) |
| Full suite | `uv run pytest -v` | all pass |
| Type check | `uv run mypy scripts/agent/orchestrator.py` | 0 new errors |
| Lint | `uv run ruff check scripts/agent/orchestrator.py` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Workflow task created | integration test: run `handle_turn` → check `workflow.sqlite` tasks table | 1 row inserted |
