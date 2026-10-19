## Goal

Create `tests/mcp_servers/lifespan_fixtures.py`, a test-only fixture module exposing a
FastAPI app whose lifespan raises during startup (for `REQ-002`) and a healthy-lifespan
FastAPI app (for `REQ-003`). Both are referenced by the regression tests via `app_module`.

## Scope

- **In-Scope**:
  - Create `tests/mcp_servers/lifespan_fixtures.py` with `failing_lifespan_app` and
    `healthy_lifespan_app`.
- **Out-of-Scope**:
  - Modifying `scripts/mcp_servers/server.py` (covered by
    `implementations/20261019-092908_01_scripts_mcp_servers_server.py.md`).
  - Adding the tests that consume the fixtures (covered by
    `implementations/20261019-092908_02_tests_mcp_servers_test_mcp_server_base.py.md`).

## Assumptions

- `tests` is importable as a package (`tests/__init__.py` exists) and `tests.mcp_servers`
  resolves as a namespace package (other tests already import
  `from tests.mcp_servers._auth_headers import ...`), so
  `tests.mcp_servers.lifespan_fixtures` is importable at test runtime.
- uvicorn resolves `app_module` through `sys.path`; the dotted path
  `tests.mcp_servers.lifespan_fixtures:<symbol>` must therefore resolve when the test sets
  it as `app_module`. Confirm this resolves on the installed uvicorn before relying on it.
- Driving the real override requires `uvicorn.Server._serve()` (which sets
  `self.lifespan`); `Server.startup()` alone raises `AttributeError` because `self.lifespan`
  is not initialized in `__init__`.

## Design decisions

- Model the failing app with an `@asynccontextmanager` lifespan that raises before `yield`;
  uvicorn's `LifespanOn` converts this into `should_exit=True` and logs its own
  `Application startup failed. Exiting.` diagnostic (verified against uvicorn 0.49.0).
- Model the healthy app with an `@asynccontextmanager` lifespan that yields immediately, so
  `super().startup()` assigns `self.servers` and sets `started=True`.

## Alternatives considered

- A plain `FastAPI()` with no lifespan for the healthy case — acceptable, but an explicit
  healthy lifespan is more parallel to the failing app and makes the intent obvious.
- Raising inside a `try/except: raise` to avoid the unreachable-`yield` lint — rejected; a
  bare `raise` before `yield` plus `# noqa: B011` is simpler and equivalent.

## Implementation

### Target file

`tests/mcp_servers/lifespan_fixtures.py` (new)

### Procedure

1. Create `tests/mcp_servers/lifespan_fixtures.py` with the header docstring noting it is a
   test-only fixture referenced via `app_module`.
2. Define the failing-lifespan app:
   ```python
   from contextlib import asynccontextmanager
   from collections.abc import AsyncGenerator

   from fastapi import FastAPI

   @asynccontextmanager
   async def failing_lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
       raise RuntimeError("simulated application startup failure")
       yield  # noqa: B011 - unreachable; forces a startup failure

   failing_lifespan_app = FastAPI(lifespan=failing_lifespan)
   ```
3. Define the healthy-lifespan app:
   ```python
   @asynccontextmanager
   async def healthy_lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
       yield

   healthy_lifespan_app = FastAPI(lifespan=healthy_lifespan)
   ```
4. Verify the failing app triggers uvicorn's startup-failure path on the installed version
   (this is what REQ-002 relies on): drive
   `uvicorn.Server(config=uvicorn.Config(failing_lifespan_app))._serve(sockets=None)` and
   confirm `should_exit` is True, `self.servers` is unset, and `started` is False.
5. Confirm `tests.mcp_servers.lifespan_fixtures` resolves via `app_module` on the installed
   uvicorn (e.g. `import_string("tests.mcp_servers.lifespan_fixtures:failing_lifespan_app")`).
6. Run the REQ-002 / REQ-003 tests in
   `implementations/20261019-092908_02_tests_mcp_servers_test_mcp_server_base.py.md` and
   confirm they pass.

### Method

- Keep the module free of production imports and side effects: only `fastapi` and
  `contextlib`. Creating the `FastAPI()` instances at import time has no runtime effect.
- The failing lifespan MUST raise before `yield` so the ASGI lifespan startup fails; the
  `# noqa: B011` silences the unreachable-`yield` lint.
- Reference each app from the tests via
  `app_module = "tests.mcp_servers.lifespan_fixtures:<symbol>"` (the dotted path, not a bare
  module name), matching how `tests.mcp_servers.*` already resolves in the test environment.

### Details

- `REQ-002`: `failing_lifespan_app` drives the real override through `run_http()` and
  produces the clean uvicorn diagnostic + `SystemExit(1)` without `AttributeError`. Covers
  AC-001, AC-003.
- `REQ-003`: `healthy_lifespan_app` reaches the normal start path where the override verifies
  the bound socket. Covers AC-002.
- Evidence (verified against uvicorn 0.49.0): driving `_serve()` with the failing lifespan
  logs `ERROR: Application startup failed. Exiting.`, sets `should_exit=True`, leaves
  `self.servers` unset, and leaves `started=False`; `Server.startup()` cannot be called
  directly because `self.lifespan` is initialized only in `_serve()`.

## Compatibility considerations

- Test-only module; no production impact. Referenced solely via `app_module` by the tests.

## Security considerations

- N/A: test fixtures only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/lifespan_fixtures.py` | Referenced by REQ-002 / REQ-003 tests; failing app reproduces startup failure | `uv run pytest tests/mcp_servers/test_mcp_server_base.py` | Fixtures resolve; new tests pass |

## Completion criteria

- `AC-003`: `failing_lifespan_app` reproduces the failing-lifespan case (uvicorn diagnostic +
  no `AttributeError`) when driven through `run_http()`.
- The healthy app reaches the normal start path so the REQ-003 loopback verification runs.

## Out of scope

Modifying `scripts/mcp_servers/server.py` or adding the consuming tests (each has its own
procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261019-193849 | Created tests/mcp_servers/lifespan_fixtures.py with failing_lifespan_app (raises before yield) and healthy_lifespan_app (yields immediately). |
| 2 | Add or update tests per Validation plan | Completed | — | 20261019-193849 | N/A: fixture module only; consumed via app_module by procedure 092908_02. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261019-193849 | Fixtures resolve via uvicorn import_string(app_module); REQ-002/REQ-003 tests pass. ruff clean. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261019-193849 | No doc changes. |

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
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: issues/20261018-191418_mcp001_mcp-server-startup-lifespan-failure-raises-attributeerror-masking-uvicorn-diagnostic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-232138_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-092908
- **Related target files**: tests/mcp_servers/lifespan_fixtures.py
