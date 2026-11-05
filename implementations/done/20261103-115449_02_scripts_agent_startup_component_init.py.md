## Goal

Make `ComponentInitializer.initialize` close the leaked-window client: register the seq 01
factory hook so the initializer remembers the `httpx.AsyncClient` the moment it is created,
and when `_initialize` raises while `ctx.services` is still `None`, await `aclose()` on it
(containing any `aclose` failure with a log line) before re-raising the original exception
unchanged, including `BaseException` subclasses such as `StartupInterrupted` (REQ-002,
REQ-003; AC-002, AC-003, AC-004).

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/startup_component_init.py` row (seq 02) and its companion test
row `tests/agent/test_startup_component_init.py` (seq 04, new file, companion-eligible, no
document of its own) of
`plans/20261101-144316_factorycleanup001_factory-leaks-client-on-build-failure.md`. Runs
after `implementations/20261103-115449_01_scripts_agent_factory.py.md` — the
`on_client_created` (new) keyword it passes is declared there — and is the last code document of
the plan before the plan-wide validation.

## Assumptions
- Verified against current source (20261103): `initialize` (startup_component_init.py:39)
  is `async`, calls the synchronous `_initialize` (51) then the `self._cmds`/
  `self._orchestrator` `RuntimeError` guard and returns; `_initialize` (51-62) calls
  `self._view.setup_readline()`, `build_agent_context(ctx, self._view)` (55), then
  `build_llm_url`, `_init_command_registry`, `_check_workflow_definition`,
  `_check_workflow_schema`, `_init_orchestrator`. `StartupInterrupted` subclasses
  `BaseException` (`scripts/agent/startup.py`), so an `except Exception` would miss it —
  the Plan's REQ-002 names `BaseException` explicitly.
- radon today: `initialize` A(3) (Plan's 20261103 correction; the Plan's Design text said
  A(1) — corrected in the Plan's Assumptions). The try/except + cleanup branches must keep
  `initialize` at rank A (estimated A(5) ceiling).
- `startup_component_init.py` is 3672 B (gate 20480 B) — ample; module has no
  `collections.abc` import yet.
- Test fixture pattern: `tests/agent/test_startup_workflow_preflight.py:21` builds
  `ComponentInitializer(MagicMock ctx, MagicMock view)`; a `MagicMock` ctx has a truthy
  `services`, so cleanup tests must set `ctx.services = None` explicitly (Plan Reference
  Files note). `tests/agent/test_startup_rollback.py::test_no_rollback_on_initialize_failure`
  (159) patches `ComponentInitializer.initialize` wholesale and is unaffected.
- `on_client_created` (new) is declared by the earlier sibling document (seq 01); this
  document adds `_exposed_http` (new), `_on_client_created` (new) and `_close_exposed_client` (new).
- Gated plan: the six unresolved startup issues named in the Plan's Dependencies section
  are not prerequisites per the Plan; each Pending row carries a `Gated:` note and
  scheduling is the owner's decision.

## Design decisions
- Remember the client in a new instance attribute `self._exposed_http: httpx.AsyncClient |
  None = None` (new) set by a new bound method `_on_client_created(self, client)` (new),
  passed as `on_client_created=self._on_client_created` to `build_agent_context` inside
  `_initialize` — a bound method over a lambda for mypy cleanliness (plain attribute
  assignment inside a lambda would be `object`-typed).
- Cleanup lives in `initialize` (not `_initialize`): wrap `self._initialize()` in
  `try/except BaseException`, and in the handler call a new
  `async def _close_exposed_client(self)` (new) when `self._ctx.services is None and
  self._exposed_http is not None`, then bare-`raise`. The post-assignment case and the
  success case take no extra action (REQ-003; `close_resources()` owns the assigned case).
- `_close_exposed_client` (new) awaits `self._exposed_http.aclose()` inside `try/except
  Exception` with a `logger.warning(..., exc_info=True)` line naming the startup-failure
  cleanup; an `aclose` failure never replaces the original exception (REQ-002; AC-003). The
  contained type is `Exception`, per the Plan's Risks mitigation (a second cancellation
  during the close propagates and the process-exit bound applies).
- The `RuntimeError` cmds/orchestrator guard in `initialize` stays outside the try: it can
  only fire after `_initialize` returned, i.e. after `ctx.services` was assigned, so it is
  REQ-003 territory closed by `close_resources()`.

## Alternatives considered
- `except Exception` instead of `except BaseException`: rejected — `StartupInterrupted`
  subclasses `BaseException` (verified 20261103) and REQ-002 names it.
- Closing in `StartupOrchestrator.run`: rejected by the Plan (Design alternatives (a));
  `startup.py` stays untouched (REQ-003).
- `contextvars` or a pending-client field on `AgentContext`: rejected — Plan alternative
  (b) is the recorded fallback only if UNK-01 is answered that way; the instance attribute
  keeps the state where the cleanup happens.

## Implementation
### Target file
`scripts/agent/startup_component_init.py`

### Procedure
1. Confirm the red companion tests (see Companion test files) exist and fail against the
   current `initialize`.
2. Add `from collections.abc import Callable` to the imports (for the hook parameter
   typing) and extend `__init__` (33-37) with `self._exposed_http: httpx.AsyncClient | None
   = None`.
3. Add the method `_on_client_created(self, client: httpx.AsyncClient) -> None` (new):
   one-line assignment `self._exposed_http = client`, docstring naming the leak window it
   covers.
4. In `_initialize`, change the factory call (55) to
   `build_agent_context(ctx, self._view, on_client_created=self._on_client_created)`.
5. In `initialize`, wrap `self._initialize()` (43) in `try/except BaseException:`; in the
   handler, if `self._ctx.services is None and self._exposed_http is not None`, `await
   self._close_exposed_client()`, then bare `raise`.
6. Add `async def _close_exposed_client(self)` (new) per Design decisions, with the
   contained `aclose()` and the warning log line.

### Method
One attribute, two small methods, one keyword added to the existing factory call, and one
try/except wrapper in `initialize`; `_initialize`'s step sequence and `startup.py` are
untouched (REQ-003).

### Details
- Log line wording: state that the client exposed during a failed startup initialization
  was closed after an `aclose()` failure; include the session/none context if trivially
  available — keep the message free of user data (no new masking obligation; the client
  object carries no payload).
- radon: `initialize` A(3) → estimated A(5) (try/except, two `and` conditions, contained
  close); recheck `uv run radon cc scripts/agent/startup_component_init.py -s -n C` — no
  B-or-worse function allowed.
- `Callable` import usage: the hook attribute can be typed implicitly; if mypy infers
  fine without the import, skip the import instead of adding an unused one (vulture/ruff
  F401 gate) — decide at implementation, record the outcome in Notes.

### Companion test files
- `tests/agent/test_startup_component_init.py` (new) (companion of the
  `scripts/agent/startup_component_init.py` row; Plan `Implementation Target Files` seq 04
  covered here per the companion rule; the file does not exist today — verified 20261103)
  - Procedure: create the module with an async-test class using the preflight-fixture
    pattern (MagicMock `ctx` with `ctx.services = None`, MagicMock `view`), patching
    `agent.startup_component_init.build_agent_context` with a fake that records the
    received `on_client_created` (new) argument and (for failure tests) invokes it with a stub
    client whose `aclose` is an `AsyncMock` before raising the injected error:
    (i) `test_pre_assignment_failure_closes_exposed_client` (new): fake factory calls the
    hook then raises `RuntimeError("builder failed")`; assert `initialize()` raises the
    same exception object and `aclose` was awaited once (REQ-002; AC-002).
    (ii) `test_aclose_failure_does_not_mask_original` (new): same, `aclose` side_effect
    `RuntimeError("close failed")`; assert the original exception object propagates and
    the warning log is emitted (`caplog`) (REQ-002; AC-003).
    (iii) `test_base_exception_re-raised_after_close` (new): injected
    `StartupInterrupted` (imported from `agent.startup`); assert it propagates unchanged
    after `aclose` was awaited (REQ-002).
    (iv) `test_post_assignment_failure_closes_nothing` (new): fake factory assigns a
    sentinel to `ctx.services` before the injected later-step failure (patch
    `_init_command_registry` to raise instead); assert `aclose` was never awaited (REQ-003;
    AC-004).
    (v) `test_success_closes_nothing` (new): fake factory completes normally (sets
    `ctx.services` sentinel; patch the registry/preflight/orchestrator methods so no real
    wiring runs, mirroring `test_startup_workflow_preflight.py`); assert no `aclose`
    (REQ-003; AC-004).
  - Validation: `uv run pytest tests/agent/test_startup_component_init.py -q` — red before
    Procedure 2-6, green after.

## Compatibility considerations
- `tests/agent/test_startup_rollback.py` patches `initialize` wholesale (verified 20261003
  re-run 20261103) — unaffected; `test_startup.py`,
  `test_startup_workflow_preflight.py`, `test_repl.py`,
  `test_resource_shutdown_coordinator.py` must keep passing unchanged (AC-006 regression
  run).
- UNK-01 (owner confirmation of the cleanup owner) is non-blocking; this document
  implements the Plan's chosen owner (`initialize`), and the Plan's fallback (b) shares the
  seq 01 factory-side step.
- No `docs/` change (Plan Documentation Impact N/A); `uv run python
  tools/generate_reference_table.py --check` at validation (new methods are
  underscore-private — no regeneration expected).

## Security considerations
- The cleanup log line names only internal state (startup failure, close failure); no
  user data, no new trust-boundary crossing.

## Rollback considerations
- Single-file change plus new test module; revert the commit restores today's `initialize`.

## Validation plan
1. `uv run pytest tests/agent/test_startup_component_init.py -q` — red before Procedure
   2-6, green after (Validation plan row 2).
2. Regression: `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_startup.py
   tests/agent/test_startup_workflow_preflight.py tests/agent/test_repl.py
   tests/agent/test_resource_shutdown_coordinator.py -q` — all pass, rollback behavior
   unchanged (AC-006; Validation plan row 3).
3. Static: `uv run ruff check scripts/agent/startup_component_init.py
   tests/agent/test_startup_component_init.py`, `uv run ruff format --check` on both, `uv
   run mypy scripts/agent/startup_component_init.py`, `uv run bandit -r
   scripts/agent/startup_component_init.py -c pyproject.toml` (no new finding), `uv run
   radon cc scripts/agent/startup_component_init.py -s` (`initialize` stays rank A), `uv
   run python tools/check_module_size.py`, `uv run lint-imports` (contracts kept).
4. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after
   both documents of this plan are executed.

## Completion criteria
- AC-002: on a pre-assignment `_initialize` failure the exposed client's `aclose()` is
  awaited before the original exception reaches the caller, same exception object.
- AC-003: an `aclose()` failure is logged and never replaces the original exception.
- AC-004: post-assignment failure and success paths await no `aclose()`;
  `StartupOrchestrator.run` and its rollback are untouched and the regression files pass
  unchanged (AC-006).

## Out of Scope
- The factory hook itself (`scripts/agent/factory.py`, seq 01) and its tests.
- `scripts/agent/startup.py`, `scripts/agent/repl.py`,
  `scripts/agent/resource_shutdown_coordinator.py`, `scripts/agent/context.py` (read-only
  Reference Files).
- The six unresolved startup issues under the Plan's Dependencies (gated scheduling).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create red `tests/agent/test_startup_component_init.py` (new), confirm it fails (Procedure 1; Companion test files) | Completed | 20261105 | 20261105 | New module created with 5 tests (pre-assignment close, aclose-failure-not-masking, BaseException re-raise, post-assignment closes nothing, success closes nothing); red before implementation, green after (5 passed). |
| 2 | Implement attribute, hook method, factory keyword, try/except and contained close (Procedure 2-6) | Completed | 20261105 | 20261105 | Added `_exposed_http`, `_on_client_created`, `_cleanup_on_failure` (`except BaseException` + pre-assignment guard), `_close_exposed_client` (contained `aclose` + warning). `Callable` import skipped — no `Callable` annotation in this module (hook passed as bound method); ruff F401 clean. mypy clean; radon `initialize` A(4) (within A(5) ceiling). |
| 3 | Run this document's checks and the startup regression set (Validation plan 1-3) | Completed | 20261105 | 20261105 | 5 new + 151 regression tests pass; `ruff check/format` clean, `mypy` clean, radon `initialize` rank A, bandit no findings, `check_module_size` OK (3672 B), `lint-imports` 6 contracts kept. |

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
- **Requirement ID**: REQ-002 (close the exposed client on a pre-assignment failure,
  contained `aclose`, unchanged re-raise including `BaseException`), REQ-003 (no close on
  the assigned/success cases, `startup.py` untouched), REQ-004 (the new test module)
- **Source issue**: issues/20261003-180345_factorycleanup001_factory-leaks-client-on-build-failure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-144316_factorycleanup001_factory-leaks-client-on-build-failure.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-115449
- **Related target files**: `scripts/agent/startup_component_init.py`, `tests/agent/test_startup_component_init.py`
