## Goal

Make `StartupOrchestrator.run` honor a shutdown request at every awaited stage and at every stage boundary: the stage in progress is cancelled, the servers started so far are rolled back through the existing branch, and startup ends with `StartupInterrupted` before the banner or a session start (`REQ-001`: stage cancellation; `REQ-002`: boundary checks; `REQ-004`: no change without a request; `REQ-005`: stage tests).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: `StartupOrchestrator` in `scripts/agent/startup.py` (a private stage-race helper, a private boundary check, their use in `run`) and the companion test file `tests/agent/test_startup_rollback.py`.
- Out of scope: `SignalHandler` and the Windows fallback, the input loop after startup, `ComponentInitializer.initialize` and the config-only stage (synchronous and bounded, covered by boundary checks only), making individual probes event-aware, and the RAG stop mechanism (document `02`).

## Assumptions

- Plan overlap judgment: this file is a target of this Plan only. The Plan's REQ-003 consumes the RAG stop event that Plan `startrev006` adds; that dependency affects document `02` only, so this document has no ordering constraint against Plan `startrev006`.
- `shutdown_event` is held as `self._shutdown_event` and is passed today only to `McpServerStarter`; the other collaborators are built without it (read in Step 3a).
- `StartupInterrupted` derives from `BaseException`, so the generic `except Exception` in `run` does not catch it and the dedicated `except StartupInterrupted` branch performs the rollback and re-raises.
- A boundary check placed before `_start_servers` runs inside the `try`, so a request seen there calls `lifecycle.shutdown_all()` although nothing was started; that call is idempotent and reports nothing when no server is tracked.
- `scripts/agent/startup.py` is 6993 bytes against a 24576 byte module size limit, so the additions fit without a split.
- Test file `tests/agent/test_startup_rollback.py` is a companion: it is a Plan row under `tests/`, only the `startup.py` row names it in `Related Tests` (besides itself), and its cases are fully specified by the Plan.

## Design decisions

- Add a private async helper `_run_stage` (new) that wraps the stage coroutine in a task, waits on the task and a task for `self._shutdown_event.wait()` with `asyncio.wait(..., return_when=FIRST_COMPLETED)`, and returns the stage result when the stage wins. When the event wins it cancels the stage task, awaits it so its cleanup runs, swallows its `CancelledError`, and raises `StartupInterrupted` naming the stage. With no event configured it simply awaits the stage.
- Add a private helper `_raise_if_shutdown_requested` (new) that raises `StartupInterrupted` naming the boundary when the event is set; call it before `_start_servers`, between each pair of stages, and after the last stage inside the same `try`, so the existing rollback branch handles every case.

## Alternatives considered

- Passing the event into every probe, discovery call and prompt setup: rejected in the Plan (several signature changes, each new probe must remember the check).
- Boundary checks only: rejected, a hung probe would still block.

## Implementation
### Target file
`scripts/agent/startup.py`

### Procedure
1. Add the two private helpers `_run_stage` (new) and `_raise_if_shutdown_requested` (new) to `StartupOrchestrator`.
2. In `run`, call the boundary check `_raise_if_shutdown_requested` (new) with the boundary name "startup" first inside the `try`, then keep `_start_servers` and `_verify_mcp_health` as they are (the starter already observes the event).
3. Replace `await self._check_services()` and `await self._setup_prompt()` with `await self._run_stage("service validation", self._check_services())` and `await self._run_stage("prompt setup", self._setup_prompt())`, with `_raise_if_shutdown_requested` (new) calls between them and after the last stage, all inside the `try`.

### Method
- If the coroutine running `run` is itself cancelled while waiting inside `_run_stage`, cancel the stage task and the event-wait task before re-raising, so nothing is left running; cancel the event-wait task whenever it is not the winner.
- An exception raised by the stage at the same moment the event is set is propagated as raised; the event is honored at the next boundary check. Do not wrap or mask stage exceptions.
- Keep messages short and in English; the `StartupInterrupted` text names the stage or boundary.

### Details
- The stage task is created with `asyncio.ensure_future`; await it after cancelling so executor hand-offs and `finally` blocks complete (this is what lets the RAG step in document `02` set its stop event).
- Keep `_check_services` and `_setup_prompt` unchanged; only their call sites in `run` change.
- Radon: every method in this module is A or B today; keep both new helpers at B or better.

### Companion test files
- `tests/agent/test_startup_rollback.py`
  - Procedure: write these first and confirm they fail on the current code, using `_make_rollback_startup` and the file's component-init stub fixture, with a real `asyncio.Event` passed as the orchestrator's shutdown event: (a) an event set while `_check_services` blocks (a coroutine awaiting a never-set future) ends `run` with `StartupInterrupted` within a short bound, the blocked stage sees `CancelledError`, and `shutdown_all` is awaited once; (b) the same for `_setup_prompt`; (c) an event set during `_start_servers` or `_verify_mcp_health` (replaced by coroutines that set it) stops before `_check_services` starts; (d) an event set by the last stage ends `run` with `StartupInterrupted` instead of returning `(cmds, orchestrator)`; (e) with no event set the stage order and results are unchanged and a stage exception still triggers the generic rollback; (f) a stage that completes normally returns its result unchanged. Keep the existing tests untouched.
  - Validation: `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_startup.py tests/agent/test_repl.py -q`.

## Compatibility considerations

- Without a shutdown request the stage order, outcomes and exceptions are unchanged. `AgentREPL.run` still warns and re-raises `StartupInterrupted`, and `main` still returns quietly with status 0.
- No signature changes to the services, the pipeline, `PromptSetup` or `SignalHandler`.

## Security considerations

- N/A: no new input; the change only stops work earlier. A cancelled stage never leaves tools registered for use because startup aborts and the rollback plus resource closing run on every exit path.

## Rollback considerations

- Revert the commit; document `02` is independent of this file and can stay.

## Validation plan

- `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_startup.py tests/agent/test_repl.py -q`; the stage-interruption tests fail on the pre-change code.
- `uv run ruff format`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`.
- `uv run python tools/check_module_size.py`, `uv run python tools/generate_reference_table.py --check`; diff coverage per `rules/toolchain.md` section 7.

## Completion criteria

- A shutdown request set while `_check_services` or `_setup_prompt` blocks ends `run` with `StartupInterrupted` within a short bound, the stage is cancelled, and `shutdown_all` is awaited once (`REQ-001`, AC-1).
- A request set between stages or after the last stage ends `run` with `StartupInterrupted` before the next stage starts and before `run` returns (`REQ-002`, AC-2).
- With no request, behavior is unchanged and the existing tests pass (`REQ-004`, AC-4); the new tests exist and fail on the pre-change code (`REQ-005`, AC-5).

## Out of Scope

- RAG cancellation, documentation, signal registration, post-startup input loop handling, and deployment.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write the stage-interruption and boundary tests first and confirm they fail (companion `tests/agent/test_startup_rollback.py`) | Pending | — | — | |
| 2 | Add the stage helper and the boundary checks, and apply them in `run` | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (stage cancellation), `REQ-002` (boundary checks), `REQ-004` (no change without a request), `REQ-005` (stage tests)
- **Source issue**: issues/20261115-214904_startrev004_startup-ignores-shutdown-signal.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261115-221200_startrev004_startup-ignores-shutdown-signal.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261116-095731
- **Related target files**: `scripts/agent/startup.py`, `tests/agent/test_startup_rollback.py`
