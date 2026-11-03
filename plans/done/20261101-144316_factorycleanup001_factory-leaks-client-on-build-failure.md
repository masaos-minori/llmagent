## Goal
- Guarantee that the shared `httpx.AsyncClient` created by `build_agent_context()` is closed (awaited) before the startup exception propagates when a later builder step raises inside the factory, by exposing the client to the async caller (`ComponentInitializer.initialize`) at the moment it is created, without awaiting inside the synchronous factory and without changing the builder order, the `ctx.services` assignment timing, or the existing rollback of started servers.

## Priority
Low

## Scope
- **In-Scope**:
  - `build_agent_context` / `_build_llm_client`: an optional, keyword-only notification hook invoked right after the `httpx.AsyncClient` is constructed (before `LLMClient` is built), default `None` so every existing caller is unchanged.
  - `ComponentInitializer.initialize`: register the hook, and when `_initialize` raises while `ctx.services` is still `None`, await `aclose()` on the exposed client, contain any `aclose` failure (log it), and re-raise the original exception unchanged.
  - Regression tests for the factory hook and for the initializer cleanup, including the post-assignment case (no double close) and the success case.
- **Out-of-Scope**:
  - Rollback of started MCP servers (`StartupOrchestrator._rollback_servers`, existing behavior); `scripts/agent/startup.py` is not modified.
  - Failures after `ctx.services` is assigned (command registry, workflow definition/schema checks, orchestrator init): they are already closed by `ResourceShutdownCoordinator.close_resources()` in `AgentREPL.run`'s `finally` (see Problem), so no new code is added for them.
  - Retrying startup in-process; changing builder order; changing `AppServices` or `AgentContext`.
  - The open startup-review issues listed under Dependencies.
- **Dependencies**: The Issue's own Dependencies are `N/A: none`. Related open Issues (no Plans yet, none is a prerequisite of this Plan; none is in this series):
  - `issues/20261031-135544_interruptexit001_startup-interrupt-exits-traceback.md` concerns the process entry handling of `StartupInterrupted` after `AgentREPL.run` has finished its `finally` cleanup. It does not change `ComponentInitializer`, but a `StartupInterrupted`/`BaseException` raised inside the initialization window would pass through this Plan's `except BaseException` cleanup; the re-raise must stay unchanged so that Issue's contract (warn, clean up, re-raise) is not disturbed.
  - `issues/20261031-135634_validorder001_config-validation-after-spawn.md` would reorder `StartupOrchestrator.run` so configuration-only validation runs before the side-effecting steps. If it moves checks into or before `ComponentInitializer.initialize`, the cleanup here still applies (it is keyed to `ctx.services is None`); if it changes what rollback covers, re-check REQ-003 (no double close, rollback intact). No ordering requirement either way.
  - `issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md` concerns lifecycle/rollback of MCP subprocesses on the startup failure path (`_rollback_servers`, `close_resources`); disjoint from the HTTP client and from this Plan's files.
  - `issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md`, `issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md` and `issues/20261031-135607_wfschema001_schema-preflight-creates-database.md`: `wfschema001` concerns `_check_workflow_schema`, a step inside the same `_initialize` sequence but after the factory returns (so after `ctx.services` is assigned, not covered here); the other two concern server start and validation after `initialize`. No interaction with this Plan.
  - Other active Frozen Plans: none targets `scripts/agent/factory.py`, `scripts/agent/startup_component_init.py`, `tests/agent/test_agent_factory.py` or `tests/agent/test_startup_component_init.py` (Step 8b, `tools/check_plan_target_overlaps.py`).

## Background
`build_agent_context()` in `scripts/agent/factory.py` is a synchronous `def`. It builds the audit logger, then creates the shared `httpx.AsyncClient` inside `_build_llm_client`, then calls `_build_tool_executor`, `_build_history_manager` and `_build_memory_services`, and only then assigns `ctx.services` (an `AppServices` built together with `RepositoryGateway`). Its only production caller is `ComponentInitializer._initialize` in `scripts/agent/startup_component_init.py` (the Issue's Target Files attribute `ComponentInitializer._initialize` to `startup.py`; it lives in `startup_component_init.py`). `StartupOrchestrator.run` in `scripts/agent/startup.py` awaits `ComponentInitializer(...).initialize()` before its `try`, so the server rollback does not cover initialization. `AgentREPL.run` in `scripts/agent/repl.py` wraps startup and the session in one `finally` that awaits `ResourceShutdownCoordinator.close_resources()`, which closes `ctx.services.http` when `ctx.services` is set and logs "No services available to shut down" when it is `None`. `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` ("Resource Cleanup on Shutdown") states that resources are closed when startup fails or is interrupted.

## Problem
Verified against current source (Step 2/3), with one correction to the Issue:
- Confirmed: if any step after `_build_llm_client()` raises inside `build_agent_context()` (`_build_tool_executor`, `_build_history_manager`, `_build_memory_services`, `RepositoryGateway(...)` or the `AppServices` invariant check), `ctx.services` is still `None`, so the client is held only by a local variable and by builder objects. Nothing closes it: `close_resources()` skips the service shutdown for `ctx.services is None`, and `httpx.AsyncClient.aclose()` is a coroutine that cannot be awaited in the synchronous factory. Impact is low: a startup failure ends the process and the OS reclaims the socket; the visible effect is a `ResourceWarning`. It would matter only if startup were ever retried in-process (no such caller exists today).
- Correction: the Issue says the leak window also covers the `_initialize` steps after `build_agent_context()` (command registry, workflow definition and schema checks, orchestrator initialization). That does not hold on the production path: once `build_agent_context()` returns, `ctx.services` is assigned, and `AgentREPL.run`'s `finally` runs `close_resources()`, whose concurrent service shutdown awaits `svc.http.aclose()` on every exit path including a startup failure (`tests/agent/test_repl.py` pins that `close_resources` is awaited on an interrupted startup, and `tests/agent/test_resource_shutdown_coordinator.py` / `tests/agent/test_repl.py` cover the `http.aclose()` step). The leak window is therefore only the interval inside `build_agent_context()` between client creation and the `ctx.services` assignment. Within that window the client is also not reachable by `LLMClient` construction failure (the client exists before `LLMClient(...)` is called), which is why the hook fires immediately after client creation.
- Correction: the Issue's Testing Expectations name `tests/agent/test_factory.py`; that file does not exist. The factory tests are in `tests/agent/test_agent_factory.py` (`TestBuildAgentContext`), and no `ComponentInitializer` cleanup test exists yet (`tests/agent/test_startup_rollback.py::test_no_rollback_on_initialize_failure` pins that an `initialize()` failure does not roll back servers, and patches `ComponentInitializer.initialize` wholesale, so it is unaffected).

## Reason for Change
Make "resources are closed when startup fails" true for the one window where it is not, and make the cleanup ownership explicit and tested, so a future in-process retry or a changed shutdown path cannot reintroduce an unclosed client. Priority stays Low: process exit reclaims the socket today.

## Implementation Intent
Expose the client early, close it at the async caller. The factory gains an optional keyword-only hook that receives the freshly created `httpx.AsyncClient`; it is called inside `_build_llm_client` immediately after the client is constructed and before any code that can fail. `ComponentInitializer.initialize` passes a hook that remembers the client. If `_initialize` raises while `ctx.services` is still `None`, `initialize` awaits `aclose()` on the remembered client (containing any `aclose` error with a log line), then re-raises the original exception. When `ctx.services` is already assigned, `initialize` does nothing extra, because `close_resources()` owns that case; this prevents a second close and leaves `StartupOrchestrator.run` and its rollback untouched.

## Requirements
- `REQ-001`: `build_agent_context` accepts an optional keyword-only hook (default `None`) that is invoked with the `httpx.AsyncClient` right after it is created and before `LLMClient` or any later builder runs; with the hook omitted, behavior, builder order and `ctx.services` assignment timing are unchanged. No `await` is introduced in the factory.
- `REQ-002`: `ComponentInitializer.initialize` closes (awaits `aclose()`) the client exposed through the hook when `_initialize` raises while `ctx.services is None`, before the exception propagates; the original exception (including `BaseException` subclasses such as `StartupInterrupted`) is re-raised unchanged, and an `aclose()` failure is logged and never replaces it.
- `REQ-003`: When `_initialize` raises after `ctx.services` was assigned, `initialize` does not close the client (left to `close_resources()`), a successful `initialize` closes nothing, and `StartupOrchestrator.run`'s server rollback is unchanged and not run twice (no change to `scripts/agent/startup.py`).
- `REQ-004`: Regression tests cover: the hook is called with the created client before the later builders run; a later builder raising inside the factory leaves the hook-exposed client; `initialize` closes that client and re-raises the original error; an `aclose` failure does not mask it; the post-assignment failure and success cases close nothing in `initialize`.

## Implementation Target Files
**Freeze status**: Frozen

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/agent/factory.py | Add the optional keyword-only client-created hook to `build_agent_context` and thread it into `_build_llm_client`, calling it right after `httpx.AsyncClient(...)` is built | The client is created in `_build_llm_client` and not reachable by the caller until `ctx.services` is assigned; the hook is the expose-early option the Issue names | REQ-001; AC-001, AC-005 | `build_agent_context` is a synchronous `def` that calls `_build_llm_client`, `_build_tool_executor`, `_build_history_manager`, `_build_memory_services` and assigns `ctx.services` last; `_build_llm_client` constructs `httpx.AsyncClient` before `LLMClient` (checked in Step 2 and Step 3) | `tests/agent/test_agent_factory.py` | Verified |
| scripts/agent/startup_component_init.py | Register the hook in `ComponentInitializer`, and in `initialize` close the exposed client on a pre-assignment `_initialize` failure, contained and re-raising | The async caller of the factory (`initialize`) is the only place that can await `aclose()`; `_initialize` is synchronous | REQ-002, REQ-003; AC-002, AC-003, AC-004 | `initialize` is `async` and calls the synchronous `_initialize`, which calls `build_agent_context(ctx, self._view)` then the registry/preflight/orchestrator steps; this is the only production caller of `build_agent_context` (checked in Step 3 with `rg`) | `tests/agent/test_startup_component_init.py` | Verified |
| tests/agent/test_agent_factory.py | Add hook tests to `TestBuildAgentContext` (called with the created client, before later builders, absent hook unchanged) | Existing class covers `build_agent_context` with a patched-dependency fixture (`_apply_patches`, `_make_ctx`); no test covers a mid-factory failure or the hook | REQ-004; AC-001, AC-005, AC-006 | `TestBuildAgentContext` tests use `_apply_patches(monkeypatch)` over `_FACTORY_PATCHES` and assert `httpx.AsyncClient` is created once (checked in Step 2) | `TestBuildAgentContext` tests in this file | Verified |
| tests/agent/test_startup_component_init.py | New file: tests for `ComponentInitializer.initialize` cleanup (pre-assignment failure closes and re-raises; `aclose` failure does not mask; post-assignment failure and success close nothing) | No existing test exercises `initialize` cleanup; `test_startup_workflow_preflight.py` covers only the preflight methods and `test_startup_rollback.py` patches `initialize` wholesale | REQ-004; AC-002, AC-003, AC-004, AC-006 | New file: its containing directory `tests/agent/` exists; confirmed `tests/agent/test_startup_component_init.py` does not exist (checked in Step 2) | the new tests in this file | Verified |

Rules (see `rules/workflow-lifecycle.md` Implementation Target Files Validation (Plan
Freeze) for the full validation procedure):
- One row per file. A directory, glob pattern (`*`, `**`), component/module name, file
  group, or a vague phrase (e.g. "related files", "as necessary", "etc.") MUST NOT
  appear as a row — list each file individually by its exact repository-relative path.
- Record a test, configuration, schema, migration, deployment, or documentation file as
  its own row when it requires modification — do not fold it into the row for the
  source file it accompanies.
- `Validation Status` is `Verified` or `Needs confirmation` per row; every row must be
  `Verified` before this section may be marked `Frozen`.

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/agent/startup.py | `StartupOrchestrator.run` awaits `initialize()` before its `try`, owns `_rollback_servers`; must stay unchanged and must not trigger a second close | REQ-003 |
| scripts/agent/repl.py | `AgentREPL.run`'s single `finally` awaits `close_resources()` on every exit path, which closes `ctx.services.http`; basis of the window correction | REQ-002, REQ-003 |
| scripts/agent/resource_shutdown_coordinator.py | `close_resources` closes `svc.http.aclose()` only when `ctx.services` is set (else logs "No services available") | REQ-002, REQ-003 |
| scripts/agent/context.py | `AgentContext.services` is `None` until the factory finishes; `AppServices` requires non-`None` `http` | REQ-002, REQ-003 |
| tests/agent/test_startup_rollback.py | Pins that an `initialize()` failure triggers no server rollback; must keep passing | REQ-003 |
| tests/agent/test_startup_workflow_preflight.py | Shows how `ComponentInitializer` is built with `MagicMock` ctx/view in tests (a `MagicMock` ctx has a truthy `services`; tests here must set `ctx.services = None`) | REQ-004 |
| tests/agent/test_resource_shutdown_coordinator.py | Existing coverage of `close_resources` and the `ctx.services = None` case | REQ-003 |
| tests/agent/test_repl.py | Pins `close_resources` awaited on startup interrupt/failure and the independent `http.aclose()` step | REQ-003 |
| docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md | States the documented cleanup-on-startup-failure contract this change makes accurate | REQ-002 |

## Acceptance Criteria
- AC-001 (REQ-001): With a hook supplied, it is called exactly once with the `httpx.AsyncClient` before `LLMClient`, `ToolExecutor`, `HistoryManager` or memory services are built; with no hook, `build_agent_context` behaves as before (all existing `TestBuildAgentContext` tests pass unchanged).
- AC-002 (REQ-002): When a later builder (injected failure) raises inside the factory during `ComponentInitializer.initialize`, `aclose()` on the exposed client has been awaited before the exception reaches the caller, and the caller receives the original exception object.
- AC-003 (REQ-002): When `aclose()` itself raises, the original startup exception still propagates and the `aclose` failure is logged.
- AC-004 (REQ-003): When `_initialize` raises with `ctx.services` already assigned (post-factory step failure), `initialize` awaits no `aclose()`; a successful `initialize` awaits none.
- AC-005 (REQ-001): The factory contains no `await` and no `asyncio` call added for this change; builder call order and `ctx.services` assignment timing are unchanged.
- AC-006 (REQ-003, REQ-004): `tests/agent/test_agent_factory.py`, `tests/agent/test_startup_component_init.py`, `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup.py` and `tests/agent/test_startup_workflow_preflight.py` pass; `StartupOrchestrator.run`'s rollback is unchanged and runs at most once.

## Tests
- `tests/agent/test_agent_factory.py` (REQ-001, REQ-004): hook called with the created client before the later builders (record call order through patched builders); hook omitted leaves the existing tests green; an injected later-builder failure leaves the hook-exposed client observable.
- `tests/agent/test_startup_component_init.py`, new (REQ-002, REQ-003, REQ-004): `initialize` with an injected failure inside the factory and `ctx.services = None` awaits `aclose()` (an `AsyncMock`) and re-raises the same exception; an `aclose` that raises does not mask the original; a failure in a post-factory step with `ctx.services` set closes nothing; success closes nothing; `BaseException` (`StartupInterrupted`) is re-raised unchanged after the close.
- Regression run (REQ-003): `tests/agent/test_startup_rollback.py`, `tests/agent/test_startup.py`, `tests/agent/test_startup_workflow_preflight.py`, `tests/agent/test_repl.py`, `tests/agent/test_resource_shutdown_coordinator.py`.

## Documentation Impact
N/A: no `docs/*.md` change is required. The Issue's "no operator-facing documentation describes this gap" is corrected: `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` already states that resources are closed on startup failure, and this change makes that statement hold for the factory window; no wording changes (REQ-002). Whether to add an explicit sentence is a docs decision for the implementation phase and is not a Requirement here.

## Assumptions
- Verified against current source again (20261103, procedure cycle): `http = httpx.AsyncClient(...)` is factory.py:95, immediately followed by the `LLMClient(...)` construction (96-108); `build_agent_context` (323) assigns `ctx.services` last (337-351); `ComponentInitializer.initialize` (startup_component_init.py:39) calls the synchronous `_initialize` (51) which calls `build_agent_context(ctx, self._view)` (55) then the registry/preflight/orchestrator steps; `StartupInterrupted` is a `BaseException` subclass (`scripts/agent/startup.py`); `tests/agent/test_startup_component_init.py` still does not exist; no active plan overlaps these four files (re-run `check_plan_target_overlaps.py` 20261103: no findings for them).
- Correction to the Design section (20261103): radon cc today is `ComponentInitializer.initialize` A(3) (not A(1)); `_initialize` and `build_agent_context` are A(1). The constraint is that `initialize` stays rank A after the try/except + cleanup branches (estimated A(5) ceiling).
- Factory-test observation wording (20261103): "an injected later-builder failure leaves the hook-exposed client" is observed in `tests/agent/test_agent_factory.py` as: the hook mock was called once with the patched `httpx.AsyncClient` mock before the injected builder raises (the client object is reachable through the recorded hook call argument); the factory itself exposes no other handle.
- `AgentREPL.run`'s `finally` is the only production path that consumes `StartupOrchestrator.run`, and it always awaits `close_resources()`; falsifiable by finding another caller of `StartupOrchestrator` or `ComponentInitializer` (checked: only `scripts/agent/repl.py` and tests).
- Closing at `ComponentInitializer.initialize` (not `StartupOrchestrator.run`) is acceptable to the owner: the orchestrator would need to learn about a client that the factory has not yet returned, and `initialize` is the direct async caller of the factory. This is the Issue's own Unresolved Question; recorded as UNK-01 (non-blocking).
- `httpx.AsyncClient.aclose()` is safe to await on a client that was never used; not exercised here (the tests use `AsyncMock`).
- No active Frozen Plan overlaps these four files (Step 8b result recorded in the cycle report: none).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Owner confirmation that the cleanup is owned by `ComponentInitializer.initialize` via an expose-early hook, rather than by `StartupOrchestrator.run` or the factory (the Issue's Unresolved Question). Plan decision: initializer, because it is the async caller adjacent to the factory and `startup.py` stays unchanged | Owner decision | Confirm at review of this Plan; the alternative (orchestrator `except` around `initialize`) cannot see a client the factory never returned, so it would need the same hook | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/agent/factory.py | Modify | Low: one optional parameter, single production caller | 5 commits | High (one author in the last 30 days; `git shortlog` shows a single person) | not applicable (rsynced) |
| scripts/agent/startup_component_init.py | Modify | Low: `initialize` is called only by `StartupOrchestrator.run` | 0 commits | High (single author) | not applicable (rsynced) |
| tests/agent/test_agent_factory.py | Modify | Low: add tests to an existing class | 4 commits | High (single author) | not applicable (rsynced) |
| tests/agent/test_startup_component_init.py | Create | Low: new test module | N/A: new file | N/A: new file | not applicable (rsynced) |

## Design
Path B (4 target files; the factory's call signature is a runtime-facing internal interface). Analysis: `lint-imports` reports 6 contracts kept, 0 broken (checked in Step 5); `build_agent_context` has one production caller; radon cc for `build_agent_context` and `ComponentInitializer._initialize` is A (1); `bandit` reports nothing on the two source files; `vulture --min-confidence 80` reports only `Callable` in `factory.py` (a false positive: it is used inside `cast("Callable[..., T]", ...)` strings) (checked in Step 5).

Design decision: where cleanup lives.
- **Decision**: an optional keyword-only hook on `build_agent_context` (threaded into `_build_llm_client`, called immediately after the client is constructed), consumed by `ComponentInitializer.initialize`, which awaits `aclose()` on a pre-assignment failure only (`ctx.services is None`).
- **Alternatives considered**: (a) `StartupOrchestrator.run` closes `ctx.services.http` in an `except` around `initialize()` (the Issue's example): rejected, because for the only real leak window `ctx.services` is `None` and the client is not reachable, so it also needs an expose-early mechanism, and for post-assignment failures `close_resources()` already closes the client, so it would add a second close; (b) a pending-client field on `AgentContext` read by `close_resources()`: viable and keeps all closing in one place, but adds state to `context.py` (also targeted by `plans/20261030-114927_wfretry001_timeout-retry-failure-propagation.md` and `plans/20261101-143236_histlock001_history-compression-bypasses-conversation-lock.md`), so it is held as the fallback if UNK-01 is answered that way; (c) fire-and-forget `create_task(http.aclose())` from the factory: rejected, an unawaited task is not guaranteed to finish before `asyncio.run` tears down the loop, and it violates "do not await inside the synchronous factory" in spirit.
- **Compatibility impact**: the new parameter defaults to `None`; the one production caller and all existing tests are unaffected; no config key, data or documented behavior changes.
- **Reversibility**: fully reversible (remove the parameter and the `except` block); no stored state.

Failure paths and lifecycle: `initialize` catches `BaseException` only to close and re-raise (never swallow); `aclose` errors are contained with a log line so the startup error stays the one reported; the close is skipped once `ctx.services` is assigned because `close_resources()` owns that case, which keeps the close count at one and leaves `StartupOrchestrator.run`'s rollback (and its test, which patches `initialize`) untouched.

## Implementation steps
1. **Phase 1: Factory hook**
   - [ ] Add the optional keyword-only client-created hook to `build_agent_context` and `_build_llm_client`; call it right after the `httpx.AsyncClient` is constructed; keep builder order, `ctx.services` assignment and the absence of `await` unchanged (REQ-001; scripts/agent/factory.py).
   - [ ] Add the factory tests: hook called once with the created client before the later builders, hook omitted unchanged (REQ-001, REQ-004; tests/agent/test_agent_factory.py).
2. **Phase 2: Initializer cleanup**
   - [ ] In `ComponentInitializer`, register the hook, and wrap the `_initialize` call in `initialize` so a failure with `ctx.services is None` awaits `aclose()` on the exposed client (contained, logged) and re-raises the original exception; do nothing when `ctx.services` is assigned or on success (REQ-002, REQ-003; scripts/agent/startup_component_init.py).
   - [ ] Add `tests/agent/test_startup_component_init.py` covering the pre-assignment close, `aclose` failure not masking, post-assignment and success closing nothing, and `BaseException` re-raise (REQ-002, REQ-003, REQ-004; tests/agent/test_startup_component_init.py).
3. **Phase 3: Verification and deployment hand-off**
   - [ ] Run the validation plan commands below, including the regression files and the diff-cover gate (REQ-003, REQ-004; scripts/agent/factory.py, scripts/agent/startup_component_init.py, tests/agent/test_agent_factory.py, tests/agent/test_startup_component_init.py).
   - [ ] Deploy is a hand-off to `skills/deploy/SKILL.md`: the change must be committed and pushed first, and deploying is the user's decision (approval gate); both source files ship through the normal rsync with no new file in `scripts/`, config key or service change (REQ-001, REQ-002; scripts/agent/factory.py, scripts/agent/startup_component_init.py).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/factory.py | Unit: hook order and default | `uv run pytest tests/agent/test_agent_factory.py` | All pass, existing tests unchanged |
| scripts/agent/startup_component_init.py | Unit: cleanup on pre-assignment failure, no double close | `uv run pytest tests/agent/test_startup_component_init.py` | All pass |
| Startup regression | Unit | `uv run pytest tests/agent/test_startup_rollback.py tests/agent/test_startup.py tests/agent/test_startup_workflow_preflight.py tests/agent/test_repl.py tests/agent/test_resource_shutdown_coordinator.py` | All pass; rollback behavior unchanged |
| Static checks | Lint/type/security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus` (per `rules/toolchain.md`), `uv run bandit -r scripts/ -c pyproject.toml`, `uv run lint-imports` | No new findings; contracts kept |
| Changed lines | Coverage | `uv run coverage run -m pytest tests/agent/test_agent_factory.py tests/agent/test_startup_component_init.py`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | At least 90 percent on changed lines (per `rules/toolchain.md`) |

## Risks
- **Risk**: A `BaseException` or cancellation arrives while `aclose()` is being awaited in the cleanup, leaving the close incomplete (low likelihood; the process is exiting) → **Mitigation**: contain only `Exception` from `aclose`, always re-raise the original; `close_resources()` is not relied on for this window, but the OS reclaims the socket on exit, which is the Issue's own impact bound.
- **Risk**: A later change makes `ctx.services` assigned earlier or reorders the factory so the pre-assignment window shrinks or grows → **Mitigation**: the cleanup is keyed to `ctx.services is None`, and the tests assert both the pre- and post-assignment cases.
- **Risk**: `validorder001` or `interruptexit001` later change `StartupOrchestrator.run`/entry handling and the cleanup runs twice or is bypassed → **Mitigation**: those Issues are recorded under Dependencies; REQ-003's tests assert at most one `aclose()` for the combined path, and `startup.py` is untouched here, so a later Plan only needs to re-run them.
- **Risk**: Adding an optional parameter to a function patched by name in tests breaks a mock-based test (`_FACTORY_PATCHES` patches factory dependencies, not `build_agent_context` itself) → **Mitigation**: default `None`; run `tests/agent/test_agent_factory.py` and the startup regression files unchanged before adding new tests.
- **Risk**: Owner prefers a different owner for the cleanup (UNK-01) → **Mitigation**: non-blocking; fallback design (b) in Design is reversible and shares the factory-side expose-early step.

## Execution Status

Table structure, status/type vocabulary, and general guidance: see
`templates/execution-status.md`.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Factory hook and its tests (scripts/agent/factory.py, tests/agent/test_agent_factory.py) | In Progress | — | — | Gated: the six unresolved startup issues named under Dependencies (interruptexit001, validorder001, mcporphan001, startretry001, disabledauth001, wfschema001) are not prerequisites per this Plan's Dependencies section; scheduling order is the owner's decision. Procedure 20261103-115449_01 generated |
| 2 | Initializer cleanup and its tests (scripts/agent/startup_component_init.py, tests/agent/test_startup_component_init.py) | In Progress | — | — | Gated: same startup-issue gate as Step 1; REQ-003's tests must be re-run if validorder001 later reorders startup. Procedure 20261103-115449_02 generated |
| 3 | Verification and deployment hand-off (all four target files) | Pending | — | — | Gated: same startup-issue gate as Step 1 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261103-115449_01_scripts_agent_factory.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261103-115449_02_scripts_agent_startup_component_init.py.md | 2 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261003-180345_factorycleanup001_factory-leaks-client-on-build-failure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261101-144316
- **Related target files**: scripts/agent/factory.py, scripts/agent/startup_component_init.py, tests/agent/test_agent_factory.py, tests/agent/test_startup_component_init.py

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Issue Implementation Intent ("expose the client before later builders run"); `_build_llm_client` / `build_agent_context` | scripts/agent/factory.py | Step 1 | AC-001, AC-005 | tests/agent/test_agent_factory.py hook tests | Derived from confirmed evidence |
| REQ-001 | Issue Testing Expectations | tests/agent/test_agent_factory.py | Step 1 | AC-001 | `uv run pytest tests/agent/test_agent_factory.py` | Derived from confirmed evidence |
| REQ-002 | Issue Required Changes (close on failure, async-capable cleanup at the caller); `ComponentInitializer.initialize` | scripts/agent/startup_component_init.py | Step 2 | AC-002, AC-003 | tests/agent/test_startup_component_init.py | Confirmed by repository evidence |
| REQ-002 | Issue Acceptance Criteria (closed before the exception propagates) | tests/agent/test_startup_component_init.py | Step 2 | AC-002, AC-003 | `uv run pytest tests/agent/test_startup_component_init.py` | Explicit in issue |
| REQ-003 | Issue Constraints (rollback intact, not run twice); window correction from `repl.py` `finally` + `close_resources` | scripts/agent/startup_component_init.py | Step 2 | AC-004, AC-006 | startup regression files | Confirmed by repository evidence |
| REQ-003 | Issue Constraints; `tests/agent/test_startup_rollback.py` | tests/agent/test_startup_component_init.py | Step 2 | AC-004, AC-006 | post-assignment and success tests | Confirmed by repository evidence |
| REQ-004 | Issue Required Changes (add a test that makes a later step raise) and Testing Expectations | tests/agent/test_agent_factory.py | Step 1 | AC-001, AC-006 | `uv run pytest tests/agent/test_agent_factory.py` | Explicit in issue |
| REQ-004 | Issue Required Changes and Testing Expectations (the `tests/agent/test_factory.py` named there does not exist) | tests/agent/test_startup_component_init.py | Step 2 | AC-002, AC-003, AC-004, AC-006 | `uv run pytest tests/agent/test_startup_component_init.py` | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261103-115449 -->
