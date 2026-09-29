## Goal
Remove `_ServerLifecycleRouter`'s private cross-class access to
`_SubprocessLifecycleManager._http_mgr` at 12 sites in `scripts/agent/factory.py`,
routing those operations through the manager's public `LifecycleManagerProtocol` surface
while preserving the protocol contract and all observable behavior (REQ-001, REQ-002,
REQ-004).

## Scope
- Modify only `scripts/agent/factory.py`: replace the 12 `_subprocess_mgr._http_mgr.*`
  accesses with manager public-surface calls; add thin documented public wrappers where no
  public equivalent exists.
- Update the router class docstring only if it describes the private-delegation mechanism.
- No changes to `lifecycle_protocol.py`, `http_lifecycle.py`, or any test/doc file.

## Assumptions
- `self._subprocess_mgr` is typed as the concrete `_SubprocessLifecycleManager`
  (factory.py:182), so adding non-protocol public methods to the manager is mypy-safe.
- External callers use only the protocol; extending the manager's non-protocol public
  surface does not affect them.
- The 12 site line numbers are current (verified against the checked-in factory.py).

## Design decisions
- Delegate directly where the manager already exposes an exact public method:
  `shutdown_all` (L116), `restart(server_key)` (L120, looks up cfg internally),
  `get_process_snapshot` (L149), `cleanup_server_resources` (L154), and
  `start_http_subprocess(server_key, cfg, shutdown_event=None)` (L139-147, same signature
  and returns the same Popen).
- Add thin documented public wrappers to `_SubprocessLifecycleManager` mirroring its
  existing delegation pattern (`get_process_snapshot` L149, `cleanup_server_resources`
  L154) for operations lacking a public equivalent: `verify_running`, `verify_running_async`,
  `get_process_info`, `list_processes`. Keep these wrappers OFF `LifecycleManagerProtocol`
  (REQ-002); they are router-only public methods.
- Keep the router's shutdown-guard/cooldown/transition wrapper intact; drive only the leaf
  ops through the manager's public surface.

## Alternatives considered
- Leave the 4 non-equivalent accesses (`verify_running`, `verify_running_async`,
  `get_process_info`, `list_processes`) reaching into `_http_mgr` with a one-line note
  instead of adding wrappers. Rejected in favor of wrappers because leaving private access
  defeats the refactor's goal; flagged as an open decision (UNK-01/UNK-03) if a wrapper is
  deemed out of scope.
- Add the new wrappers to `LifecycleManagerProtocol`. Rejected: would change the protocol
  contract (REQ-002) and force every protocol implementer to provide them.

## Implementation
### Target file
scripts/agent/factory.py

### Procedure
1. **Phase 1 — Baseline:** run `tests/agent/test_agent_factory.py` to lock current
   behavior before any change (REQ-004).
2. **Phase 2 — Replace clean passthrough delegations:**
   - L293 `await self._subprocess_mgr._http_mgr.shutdown_all()` →
     `await self._subprocess_mgr.shutdown_all()`.
   - L337 `lambda: self._subprocess_mgr._http_mgr.restart(server_key, cfg)` →
     `lambda: self._subprocess_mgr.restart(server_key)`.
   - L352 `self._subprocess_mgr._http_mgr.get_process_snapshot(server_key)` →
     `self._subprocess_mgr.get_process_snapshot(server_key)`.
   - L382 `self._subprocess_mgr._http_mgr._cleanup_server_resources(server_key)` →
     `self._subprocess_mgr.cleanup_server_resources(server_key)`.
3. **Phase 2 — Route guarded-wrapper leaves through the manager:**
   - `ensure_ready` body (L268/275/278/287): keep the shutdown-guard/cooldown wrapper;
     delegate leaf ops (see Details / UNK-01).
   - `start_http_subprocess` leaf start (L314): delegate to
     `manager.start_http_subprocess(server_key, cfg, shutdown_event=shutdown_event)`;
     resolve the Popen-return coupling at L318 (UNK-02).
4. **Phase 2 — Add thin documented public wrappers** to `_SubprocessLifecycleManager` for
   operations without a public equivalent (keep all four off the protocol):
   - `verify_running(server_key)` → `self._http_mgr.verify_running(server_key)` (covers L268).
   - `verify_running_async(server_key, cfg)` → `self._http_mgr.verify_running_async(server_key, cfg)` (covers L278).
   - `get_process_info(server_key)` → `self._http_mgr.get_process_info(server_key)` (covers L360).
   - `list_processes()` → `self._http_mgr.list_processes()` (covers L367).
5. **Phase 3 — Verify:** re-run `tests/agent/test_agent_factory.py` then the full
   `tests/agent/`; run `mypy` and `ruff` on factory.py; confirm no
   `_subprocess_mgr._http_mgr` references remain in the router except documented
   exceptions (REQ-001, REQ-004).

### Method
Behavioral-lock edits: make each replacement and verify the corresponding existing test
still passes before moving on. Prefer small, reviewable hunks. For the two coupled cases
(`ensure_ready` body, `start_http_subprocess` return), resolve the decomposition inline and
record the decision in-code.

### Details
Site-by-site mapping in `scripts/agent/factory.py`:

| Line | Current access | Resolution | Req |
|---|---|---|---|
| 268 | `_subprocess_mgr._http_mgr.verify_running(server_key)` | Add wrapper `verify_running`; route through it | REQ-001 |
| 275 | `_subprocess_mgr._http_mgr.start(...)` (in `ensure_ready`) | Delegate leaf via `manager.start_http_subprocess` | REQ-001 |
| 278 | `_subprocess_mgr._http_mgr.verify_running_async(...)` | Add wrapper `verify_running_async`; route through it | REQ-001 |
| 287 | `_subprocess_mgr._http_mgr.restart(...)` (in `ensure_ready`) | Delegate to `manager.restart(server_key)` | REQ-001 |
| 293 | `_subprocess_mgr._http_mgr.shutdown_all()` | Delegate to `manager.shutdown_all()` | REQ-001 |
| 314 | `_subprocess_mgr._http_mgr.start(...)` (in `start_http_subprocess`) | Delegate to `manager.start_http_subprocess(...)` | REQ-001 |
| 318 | `_subprocess_mgr._http_mgr._http_procs.get(...)` | Resolve via single manager call capturing Popen (UNK-02) | REQ-001 |
| 337 | `_subprocess_mgr._http_mgr.restart(...)` | Delegate to `manager.restart(server_key)` | REQ-001 |
| 352 | `_subprocess_mgr._http_mgr.get_process_snapshot(...)` | Delegate to `manager.get_process_snapshot(...)` | REQ-001 |
| 360 | `_subprocess_mgr._http_mgr.get_process_info(...)` | Add wrapper `get_process_info`; route through it | REQ-001 |
| 367 | `_subprocess_mgr._http_mgr.list_processes()` | Add wrapper `list_processes`; route through it | REQ-001 |
| 382 | `_subprocess_mgr._http_mgr._cleanup_server_resources(...)` | Delegate to `manager.cleanup_server_resources(...)` | REQ-001 |

Open decisions (resolve during implementation; do not invent behavior):
- UNK-01 — `ensure_ready` wrapper decomposition: keep the router's shutdown/cooldown logic,
  delegate only the leaf ops through the manager's public surface.
- UNK-02 — `start_http_subprocess` Popen-return coupling: avoid double-start by capturing
  the Popen from a single manager call.
- UNK-03 — keep the four new wrappers off `LifecycleManagerProtocol`.

## Compatibility considerations
- Both classes are already wired into `ToolExecutor` and used only via
  `LifecycleManagerProtocol` by external callers; no external API change.
- Existing tests reach into `_http_mgr` mocks (e.g.
  `router._subprocess_mgr._http_mgr.restart.assert_not_called()`); after refactoring they
  must still observe the same calls via the manager's real methods onto the same mock. If
  any assertion no longer holds, the behavior changed and must be fixed — it must not
  silently pass under wrong semantics.

## Security considerations
No new permissions, secrets, or network access introduced. Behavior-preserving refactor only.

## Rollback considerations
Single-file, behavior-preserving change. Revert `scripts/agent/factory.py` to the
pre-change state; existing tests restore coverage.

## Validation plan
| Target File | Strategy | Command | Expected |
|---|---|---|---|
| scripts/agent/factory.py | Unit regression | uv run pytest tests/agent/test_agent_factory.py (then tests/agent/) | All lifecycle tests pass; behavior identical pre/post |
| scripts/agent/factory.py | Typing / lint | uv run mypy scripts/agent/factory.py && uv run ruff check scripts/agent/factory.py | mypy and ruff pass |

## Completion criteria
- No remaining `_subprocess_mgr._http_mgr` references in `_ServerLifecycleRouter` except
  documented exceptions (AC-01).
- Every `LifecycleManagerProtocol` method behaves identically before/after (existing
  lifecycle tests pass) (AC-02).
- No public API added/removed outside the manager's internal surface; protocol and
  `HttpServerLifecycleManager` unchanged (AC-03).
- `mypy` and `ruff` pass on factory.py (AC-04).

## Out of scope
- Changing `HttpServerLifecycleManager` or `LifecycleManagerProtocol`.
- Collapsing the two lifecycle classes.
- Refactoring builders or `build_agent_context`.
- Any behavioral/policy change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-09-29 | 2026-09-29 | Removed all 12 `_subprocess_mgr._http_mgr.*` cross-class accesses in `_ServerLifecycleRouter`. Added 4 thin delegating wrappers (`verify_running`, `verify_running_async`, `get_process_info`, `list_processes`) to `_SubprocessLifecycleManager`. Fixed L291 coroutine-return type by wrapping the async start call in an inner `async def _start_server() -> None`. |
| 2 | Add or update tests per Validation plan | Completed | 2026-09-29 | 2026-09-29 | Behavior-preserving refactor; no new tests added. Existing `tests/agent/test_agent_factory.py` (36 tests) is the behavioral lock and still passes unchanged. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-09-29 | 2026-09-29 | `ruff format` + `ruff check`: pass. `mypy agent/factory.py` (from within `scripts/`): clean. `pytest tests/agent/test_agent_factory.py`: 36 passed. `lint-imports`: only the pre-existing `shared->agent` broken contract (unrelated). `bandit`: only pre-existing Low B404 subprocess import. Pre-existing unrelated failures confirmed on original code: `test_orchestrator.py::...test_original_config_restored_even_on_error` and the `tool_constants` dual-module mypy config error and the AsyncMock RuntimeWarnings. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-09-29 | 2026-09-29 | No user-facing docs changed. Source Plan status row updated. Procedure archived to `implementations/done/`. |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 — reduce private
  cross-class coupling while preserving the protocol contract and observable behavior
- **Source issue**: issues/20260927-205833_fac001_reduce-cross-class-private-coupling-in-factory.py-lifecycle-classes.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-103000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-143336
- **Related target files**: scripts/agent/factory.py
