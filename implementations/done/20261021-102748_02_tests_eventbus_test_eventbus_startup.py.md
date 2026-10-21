## Goal

Add a failing-lifespan regression test to `tests/eventbus/test_eventbus_startup.py` that drives the real Event Bus `_LoopbackVerifyingServer.startup` override through the real uvicorn serve path and asserts no secondary `AttributeError` is raised once the guard is in place. (REQ-002, AC-1, AC-4)

## Scope

- Modify only `tests/eventbus/test_eventbus_startup.py`: append one new test function.
- No change to `scripts/eventbus/app.py` here (the guard is the sibling document).

## Assumptions

- A missing/invalid `EVENTBUS_SCHEMA_PATH` makes the FastAPI lifespan fail at `orjson.loads(get_schema_path().read_bytes())` (lifespan startup, before the loopback check), which sets uvicorn's `should_exit` and logs `Application startup failed. Exiting.` without creating sockets.
- The subprocess exits non-zero and promptly on a failed lifespan.

## Design decisions

- Model the test's *intent* on `TestStartupOverride.test_failing_lifespan_exits_cleanly_without_attributeerror` in `tests/mcp_servers/test_mcp_server_base.py` (drive the real override, assert no `AttributeError`), but implement it as a subprocess integration test rather than the MCP in-process driver — see Details.
- Assert both halves of AC-1: the real error is logged (`Application startup failed. Exiting.`) and no `AttributeError` appears; the process exits non-zero.

## Alternatives considered

- N/A: a subprocess reproduction mirrors the existing `test_main_post_start_verification_binds_loopback` and the original incident; an in-process driver does not apply (see Details).

## Implementation

### Target file

`tests/eventbus/test_eventbus_startup.py`

### Procedure

1. Append a new test function `test_main_failing_lifespan_exits_without_attributeerror` (new) to `tests/eventbus/test_eventbus_startup.py`; the signature takes a `tmp_path` fixture.
2. Write a minimal eventbus TOML config into `tmp_path` (same fields as the existing `test_main_post_start_verification_binds_loopback`: `port`, `db_path`, `storage_dir`, `offsets_dir`, `deadletter_dir`, `max_retry`, `host = "127.0.0.1"`, `auth_token`). `db_path`/dirs must point under `tmp_path` so the lifespan reaches the schema read.
3. Set `EVENTBUS_SCHEMA_PATH` to a **nonexistent** path (e.g. `tmp_path / "missing_schema.json"`, not created) so the lifespan fails at the schema read.
4. Launch `[sys.executable, "-m", "eventbus.app"]` via `subprocess.Popen` with `cwd` = the repo `scripts/` directory and an env carrying `EVENTBUS_CONFIG_PATH` (the temp config), `EVENTBUS_SCHEMA_PATH` (the missing path), and `PATH`. Capture `stdout`+`stderr` merged (`stderr=subprocess.STDOUT`), `text=True`.
5. Wait for the process to exit (bounded `wait(timeout=...)`), then assert:
   - `"Application startup failed. Exiting."` is in the captured output (real cause logged).
   - `"AttributeError"` is **not** in the captured output (guard prevents the secondary error).
   - `proc.returncode != 0` (non-zero exit preserved).
6. Clean up the process in a `finally` (terminate/wait/kill) as the existing test does.

### Method

Append one synchronous test function using stdlib `subprocess`; no new imports beyond what the file already has (`socket`, `subprocess`, `sys`, `time`, `pathlib.Path`; add `os` or inline `__import__("os")` for `PATH` as the existing test does).

### Details

- **Why a subprocess, not the MCP in-process driver.** `TestStartupOverride` replaces `uvicorn.Server.run` with a driver that calls `srv.serve(sockets=None)` on a server instance produced by `run_http()`. The Event Bus override is a local class inside the `_main()` **function**, which builds its own `uvicorn.Config("eventbus.app:app", ...)` with a **hardcoded app module string** and calls `server.run()`. That module string cannot be swapped for a failing-lifespan fixture, so the MCP in-process driver does not transfer. A subprocess running the real `eventbus.app` entry point is the faithful way to exercise the real override end-to-end, and it matches the existing loopback integration test in this file.
- **How the failing lifespan is triggered.** The FastAPI `lifespan` (in `scripts/eventbus/app.py`) reads the envelope schema at `orjson.loads(get_schema_path().read_bytes())` before the loopback check. Pointing `EVENTBUS_SCHEMA_PATH` at a missing file raises `FileNotFoundError` there, so uvicorn logs `Application startup failed. Exiting.` and returns without creating sockets — exactly the condition that exposes the missing-`self.servers` bug.
- **Empirical confirmation against current code.** Running `EVENTBUS_CONFIG_PATH=<temp> EVENTBUS_SCHEMA_PATH=/tmp/missing.json uv run python -m eventbus.app` from `scripts/` currently prints `ERROR: Application startup failed. Exiting.` followed by `AttributeError: '_LoopbackVerifyingServer' object has no attribute 'servers'` and exits non-zero. Therefore this test FAILS against the current (unguarded) code and PASSES after the guard — satisfying AC-4.
- **AC-4 gating.** Before applying the guard, run the new test alone and confirm it fails with the `AttributeError`; after the guard, confirm it passes. Do not mark this row complete until both directions are observed.

## Compatibility considerations

N/A: the test adds coverage only; it does not alter production behavior or any existing test.

## Security considerations

N/A: the test points the subprocess at a throwaway `tmp_path` config and a missing schema; no real data or credentials are touched.

## Rollback considerations

N/A: delete the added test function.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_startup.py` — the new failing-lifespan test passes AND the existing loopback-violation (AC-2) and loopback-success (AC-3) tests still pass; no `AttributeError`.
- Confirm the new test fails against the current code first (AC-4): run it before the guard is applied.
- Lint/type: `uv run ruff format tests/` + `uv run ruff check tests/`, `uv run mypy --no-namespace-packages scripts/` (tests are covered by pre-commit mypy).

## Completion criteria

- `test_main_failing_lifespan_exits_without_attributeerror` (new) is present and green.
- It is observed failing against the unguarded code and passing after the guard (AC-4).
- The existing loopback tests in the same file still pass; `ruff`/`mypy` clean.

## Out of Scope

- The `_LoopbackVerifyingServer.startup` guard itself (`scripts/eventbus/app.py`) — separate document.
- Changing the subprocess driver pattern used elsewhere; touching the MCP base test.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the failing-lifespan regression test to `tests/eventbus/test_eventbus_startup.py` (subprocess, missing schema path) | Completed | 20261021-111324 | 20261021-111324 | REQ-002, AC-1, AC-4 Appended subprocess test; mypy cleared via int() cast in _free_loopback_port during validation |
| 3 | Run pytest: new test passes, existing loopback tests pass, no AttributeError | Completed | 20261021-111324 | 20261021-111324 | REQ-001..004, AC-2, AC-3 17 passed; ruff/mypy/scripts-439/bandit-ll/lint-imports/module-size all clean; AC-4 verified (fails w/o guard, passes w/ guard) |

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
- **Requirement ID**: `REQ-002` (with `AC-1`, `AC-4`)
- **Source issue**: `issues/20261020-115744_ebstart003_event-bus-post-start-verification-raises-attributeerror-when-lifespan-startup-fails.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261020-232535_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261021-102748
- **Related target files**: `tests/eventbus/test_eventbus_startup.py`