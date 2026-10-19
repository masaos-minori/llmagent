## Goal

Add regression tests to `tests/mcp_servers/test_mcp_server_base.py` that drive the real
`_LoopbackVerifyingServer.startup()` override (through `run_http()`) for two cases: a
FastAPI app whose lifespan raises during startup (no `AttributeError`, clean exit), and a
healthy app whose normal loopback start still performs the post-start bind verification
(including a non-loopback bind raising). (`REQ-002`, `REQ-003`)

## Scope

- **In-Scope**:
  - Add the failing-lifespan test (`REQ-002`) and the normal-loopback / non-loopback-bind
    test (`REQ-003`) to `tests/mcp_servers/test_mcp_server_base.py`.
- **Out-of-Scope**:
  - Modifying the existing `TestBindAddressValidation`, `TestConfigIsolationValidation`,
    or any other existing test.
  - Changing `scripts/mcp_servers/server.py` (covered by the sibling procedure
    `implementations/20261019-092908_01_scripts_mcp_servers_server.py.md`).
  - Creating the fixture module (covered by
    `implementations/20261019-092908_03_tests_mcp_servers_lifespan_fixtures.py.md`).

## Assumptions

- `tests` is importable as a package (`tests/__init__.py` exists) so the fixture module
  resolves via `app_module`.
- Tests run on the main thread; if signal handling under the test runner is flaky, patch
  `capture_signals` for the duration of the drive.
- Driving the real override requires replacing `uvicorn.Server.run` with an async driver
  over the real `_serve()`; `create_server` must be stubbed to avoid a real socket bind.

## Design decisions

- Drive the real `_LoopbackVerifyingServer.startup()` through `run_http()` (spy on
  `uvicorn.Server.run`) rather than copying the override body into a mirror subclass. This
  exercises the actual local-class override, avoiding divergence from live code.
- Point `app_module` at the fixture module (`tests/mcp_servers/lifespan_fixtures.py`) so the
  failing-lifespan and healthy-lifespan apps are injected without touching production code.

## Alternatives considered

- Mirror-subclass test (subclass `uvicorn.Server` with a copy of the override body) —
  rejected: it diverges from the live local-class override and would miss a regression.
- Patching `run_http()` internals directly — rejected: the override is a local class inside
  `run_http()` and is not importable by name; the only way to exercise it is through
  `run_http()`.

## Implementation

### Target file

`tests/mcp_servers/test_mcp_server_base.py`

### Procedure

1. Read `scripts/mcp_servers/server.py` lines 232-284 (`run_http()`) and
   `implementations/20261019-092908_01_scripts_mcp_servers_server.py.md` to understand the
   override, the `sys.exit(1)` tail, and how `app_module` is consumed.
2. Confirm the existing `TestBindAddressValidation` patches `uvicorn.Server.run` to a
   no-op (`_fake_run`) and never exercises the override's `startup()` early-exit branch —
   the new tests must drive the real `startup()`, not the no-op.
3. Create the async driver that replaces `uvicorn.Server.run` and runs the real
   `_serve()`:
   ```python
   async def _drive_real_run(self):
       await self._serve(sockets=None)
   ```
   and install it with
   `monkeypatch.setattr(uvicorn.Server, "run", <sync wrapper around _drive_real_run>)`,
   where the sync wrapper runs the coroutine to completion (e.g. `asyncio.run(...)` via the
   config's loop factory).
4. Add the REQ-002 failing-lifespan test:
   - Subclass `MCPServer` with `http_host = "127.0.0.1"`, a truthy `own_config_file`, and
     `app_module` pointing at the failing-lifespan fixture (e.g.
     `"tests.mcp_servers.lifespan_fixtures:failing_lifespan_app"`).
   - Stub `ConfigLoader.restrict_to` to a no-op.
   - Install the real-run driver; stub `uvicorn.Server.main_loop` to an async no-op so
     `_serve()` returns after `startup()`.
   - Assert: no `AttributeError` is raised, a `SystemExit` is raised (the
     `if not server.started: sys.exit(1)` tail), `server.started` is False, and `caplog`
     contains uvicorn's `Application startup failed. Exiting.` diagnostic.
5. Add the REQ-003 normal-path test (two variants in one test or two tests):
   - Healthy-lifespan fixture via `app_module`; stub `ConfigLoader.restrict_to`.
   - Stub `asyncio.AbstractEventLoop.create_server` to return a fake server whose
     `.sockets[0].getsockname()[0]` is a loopback address (`"127.0.0.1"` or `"::1"`).
   - Loopback variant: assert the override completes without raising.
   - Non-loopback variant: stub `create_server` so the bound address is non-loopback and
     assert the override raises `RuntimeError` matching `not loopback`.
6. Run `uv run pytest tests/mcp_servers/test_mcp_server_base.py`; confirm the new tests pass
   and all existing tests still pass unchanged.

### Method

- The override is a local class inside `run_http()`, so the ONLY way to exercise it is to
  call `run_http()` with `uvicorn.Server.run` replaced by the real-run driver. Do not
  construct `_LoopbackVerifyingServer` directly (it is not importable).
- On the normal path, `uvicorn.Server.startup()` calls
  `loop.create_server(...)`; stub `create_server` to return a fake `asyncio.Server` with a
  `.sockets` list whose socket's `getsockname()[0]` yields the address under test, so the
  override's bind check reads a deterministic value without a real bind.
- Stub `main_loop` to a no-op so `_serve()` returns immediately after `startup()` instead of
  blocking on real serving.
- Capture logs with `pytest.LogCaptureFixture` (`caplog`) to assert uvicorn's own
  diagnostic surfaces.

### Details

- `REQ-002`: the failing-lifespan test drives the real override and asserts no
  `AttributeError`, `server.started` stays False, and uvicorn's `Application startup failed.
  Exiting.` diagnostic is what surfaces (then `sys.exit(1)`). Covers AC-001, AC-003.
- `REQ-003`: the normal-path test asserts the override still verifies the bound socket is
  loopback and that a non-loopback bind raises `RuntimeError`. Covers AC-002.
- Evidence (verified against current source): `run_http()` catches only `KeyboardInterrupt`
  (line 281) then `sys.exit(1)` when `not server.started` (lines 283-284); the override
  accesses `self.servers` unconditionally (line 263); existing `TestBindAddressValidation`
  replaces `run` with a no-op and never hits the early-exit branch.
- The fixture module (`tests/mcp_servers/lifespan_fixtures.py`) is created separately; this
  document only references it via `app_module`.

## Compatibility considerations

- Purely additive tests; no production behavior changes. Existing `TestBindAddressValidation`
  and other suites are untouched.

## Security considerations

- N/A: these tests validate the loopback-only bind verification still runs; they do not
  alter any security policy.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/mcp_servers/test_mcp_server_base.py` | Unit: failing-lifespan + normal-loopback + non-loopback-bind | `uv run pytest tests/mcp_servers/test_mcp_server_base.py` | New tests pass; existing tests unchanged |
| Whole suite | Regression | `uv run pytest` | No new failures |

## Completion criteria

- `AC-001`: the failing-lifespan test passes — no `AttributeError`, `server.started` is
  False, and uvicorn's diagnostic surfaces.
- `AC-002`: the normal-loopback test passes and the non-loopback-bind variant raises
  `RuntimeError`.
- `AC-003`: the failing-lifespan test reproduces the original failure mode and now passes.

## Out of scope

Modifying existing tests, changing `scripts/mcp_servers/server.py`, or creating the fixture
module (each has its own procedure document).

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
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002`, `REQ-003`
- **Source issue**: issues/20261018-191418_mcp001_mcp-server-startup-lifespan-failure-raises-attributeerror-masking-uvicorn-diagnostic.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261018-232138_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-092908
- **Related target files**: tests/mcp_servers/test_mcp_server_base.py
