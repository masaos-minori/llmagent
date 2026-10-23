## Goal

Create `scripts/agent/stdin_reader.py`, the single blocking-stdin-read primitive that every interactive prompt routes through, so that a cancelled or abandoned read can never hold `asyncio.run()` or the interpreter exit open (`plans/20261022-040200_plan.md`, REQ-001..REQ-005; AC-1, AC-3, AC-4).

## Scope

One new module, one public class (`StdinReader`). It owns one daemon `threading.Thread` per instance, performs one blocking `input()` per request, and bridges the result back to the awaiting coroutine via `loop.call_soon_threadsafe`. No other file is modified by this row.

## Assumptions

- At most one stdin read is outstanding at a time in production (`repl_input_loop.py:_read_input` awaits its read before `read_multiline` is called; `_prompt_user_approval` runs only during a dispatch). The `RuntimeError` guard makes a violated assumption visible instead of a hang.
- Calling `input()` from a daemon thread is equivalent, for terminal behavior, to calling it from the executor threads used today (both non-main; `readline` state is process-global).
- `loop.call_soon_threadsafe()` is available on the project's loop implementations (Linux `SelectorEventLoop`, Windows event loops).

## Design decisions

- A plain daemon `threading.Thread`, not any `concurrent.futures` executor. Measured: a private pool returns the loop in 0.20 s but the process in 6.09 s, and a pool subclass whose workers are daemon still waits 6.10 s, because `_python_exit` joins every entry of `_threads_queues` regardless of the daemon flag (`/usr/lib/python3.14/concurrent/futures/thread.py:23-31`). Only a non-pool daemon thread satisfies the exit criterion (measured 0.29 s).
- Request-driven: the worker blocks on a `threading.Event` (no poll, no sleep loop, no busy wait). It performs exactly one read per request and never pre-reads a line the caller has not requested.
- Instance ownership, not a process-wide singleton: each owner holds its own instance; a reader instance is used only from the event loop that issued its request.
- Loop capture per request from `asyncio.get_running_loop()`, so a reader instance can deliver into whichever loop is currently running rather than a bound, possibly-closed loop.

## Alternatives considered

- A background thread that always reads and pushes into a queue: simpler code, but it would steal input the REPL has not requested and would make `/exit` handling depend on queue contents. Rejected.
- `loop.add_reader(sys.stdin, …)`: would bypass `readline` (losing tab completion/history), break `input()`'s EOF/Ctrl-C behavior, and is unsupported on Windows event loops. Rejected.

## Implementation

### Target file

`scripts/agent/stdin_reader.py` (new)

### Procedure

1. Create the module with one class `StdinReader`.
2. Implement the guarded, request-driven read described below.
3. Keep every function at or below radon B and the file well under the 16384 B size gate.

### Method

- `__init__(self, prompt: str = "")`: store the prompt; initialise the worker-thread bookkeeping (daemon thread handle, the "start-waiting" event, the "line-available" event, a slot for the last line/exception, and a one-request-in-flight guard). Do not start the thread here.
- `async def read(self, prompt: str | None = None) -> str`: the sole public entry. Capture `loop = asyncio.get_running_loop()`. If a request is already in flight, raise `RuntimeError`. Mark in flight, create a result future, ensure the daemon worker is started (start it once, lazily), signal it to perform one read, await the future, and on return clear the in-flight guard. Deliveries happen from the worker thread via `loop.call_soon_threadsafe`.

### Details

- **Worker thread**: started exactly once, the first time `read` is called, as `threading.Thread(target=self._run, daemon=True)`. `_run` loops: wait on the start event, perform `input(self._prompt)`, store the line or the raised exception, set the line-available event, and repeat until the interpreter exits. It never joins and is never joined.
- **Delivery**: after the worker stores a line, it calls `loop.call_soon_threadsafe(self._deliver, future)` where `_deliver` sets the future's result. Wrap the `call_soon_threadsafe` call in `try/except RuntimeError` to make delivery to a closed loop a no-op (REQ-003).
- **Cancellation / abandoned-line policy**: if the originating future is already `done()` when the line arrives, deliver to the newest pending request on the instance; if none exists, discard. This is stated in code and pinned by `TestCancelledRequestDelivery` (`AC-4`).
- **Exceptions (REQ-004)**: the worker catches `(Exception, KeyboardInterrupt, SystemExit)` explicitly around `input()` and stores the exception in the future via `loop.call_soon_threadsafe(fut.set_exception, exc)`. No blind `except Exception`; no suppression comment. This reproduces what `concurrent.futures` delivers today and what `_input_task` expects at `repl_input_loop.py:145`.
- **One-request guard (REQ-002)**: a second `read` on the same instance while one is in flight raises `RuntimeError` instead of being silently queued.
- **No lifecycle hooks**: no `close()`, `shutdown()`, `join()`, or `atexit` hook. Joining it is exactly the cost this Plan removes.

## Compatibility considerations

The class is internal to this Plan's three owners (`ReplInputLoop`, `CLIView`, and a module-level instance in `tool_approval.py`). Its public surface is a single `async read()`; callers keep their existing prompts, EOF/Ctrl-C mapping, and continuation logic unchanged. See `plans/20261022-040200_plan.md` REQ-005..REQ-009.

## Security considerations

N/A: no new network, filesystem, subprocess, or credential path. The only behavior change is which thread performs the blocking read.

## Rollback considerations

N/A: revert the commit that adds the module and rewires the three call sites.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/stdin_reader.py` | Unit: injected fake read function; request counting, concurrency guard, cancelled-request delivery, closed-loop no-op, worker survival; plus the `integration` subprocess exit measurement. | `uv run pytest tests/agent/test_stdin_reader.py -v` ; `uv run pytest tests/agent/test_stdin_reader.py -m integration -v` | All cases pass; child exits within 2.0 s while its read is still blocked; no non-daemon thread created (AC-1, AC-3, AC-4). |
| `scripts/agent/` (whole package) | Regression: exit path, signals, shutdown coordinator. | `uv run pytest tests/agent -q` ; `git diff --stat scripts/agent/repl.py` | All pass; `repl.py` shows no diff (AC-8). |
| `scripts/` static gates | Lint, types, size, complexity. | `uv run ruff format scripts/agent` ; `uv run ruff check scripts/agent` ; `uv run mypy --no-namespace-packages scripts/agent` ; `uv run python tools/check_module_size.py` ; `uv run radon cc scripts/agent -s -n C` | Clean; `stdin_reader.py` far below the size gate; no function worse than B (AC-7). |

## Completion criteria

- The module imports cleanly and exposes exactly one public class with a single `async read()` entry.
- The worker is a daemon thread started lazily on first use; no `concurrent.futures`, `asyncio.to_thread`, or `run_in_executor` is used anywhere in the module.
- The one-request guard, explicit exception tuple, closed-loop no-op, and abandoned-line delivery are each covered by a passing unit test in `tests/agent/test_stdin_reader.py`.
- The `@pytest.mark.integration` subprocess case exits within 2.0 s while its read is still blocked.

## Out of Scope

Rewiring the three call sites (that is rows 2, 3, 4). Tuning any timeout value. Removing the currently-unused `Reader` protocol or `read_multiline`'s `loop` parameter.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create `scripts/agent/stdin_reader.py` with the guarded, request-driven daemon read primitive | In Progress | 20261023-074240 | — | REQ-001..REQ-005; AC-1, AC-3, AC-4 |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: `issues/20261021-093421_repl002_cancelled_input_read_delays_process_exit.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-040200_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-074240
- **Related target files**: `scripts/agent/stdin_reader.py`
