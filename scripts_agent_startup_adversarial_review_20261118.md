# Adversarial Review — `scripts/agent` startup processing (10 modules)

Reviewed head: `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9` (working tree matched HEAD, no uncommitted edits; only untracked files are prior review reports).

## Review Scope

- Reviewed (orchestration + entry): `__main__.py`, `startup.py`, `repl.py` (run/finally wiring).
- Reviewed (component init/DI): `startup_component_init.py`, `factory.py`.
- Reviewed (MCP subprocess startup): `startup_mcp_starter.py`, `lifecycle_router.py`, `http_lifecycle.py`.
- Reviewed (validation/prompt/reporting): `startup_validation.py`, `startup_prompt_setup.py`, `startup_reporter.py`.
- Reviewed (shutdown/resource lifecycle): `resource_shutdown_coordinator.py`.
- Not reviewed: REPL command subsystem (`commands/*`), memory subpackage (`memory/*`), workflow engine (`workflow/*`), turn/tool execution loop, non-Python assets. The review is scoped to *agent startup processing* as requested.

Working tree vs reviewed head: matched at `de26cfcadb4bd7a0502c3ecd05ce1e4c09072ed9`.

## Commands run

| Tool | Scope | Result |
|---|---|---|
| `ruff check` | 9 startup/core modules | All checks passed |
| `mypy --no-namespace-packages` | 9 startup/core modules | Success: no issues found |
| `bandit -ll` | 9 startup/core modules | 0 Medium/High; 3 Low (all B404 `subprocess`, documented `# nosec`) |
| `generate_reference_table.py --check` | `scripts/agent/` guarded domain | No drift found |
| `pytest tests/agent/ -k startup|lifecycle|factory|http_lifecycle|component_init|mcp_starter` | startup-adjacent suite | 593 passed, 2 skipped |

## Summary

- Overall assessment: **Clean.** No correctness, concurrency, resource-lifecycle, error-handling, configuration, or security defect survives adversarial scrutiny across the component-init/DI, MCP-subprocess startup, validation-pipeline, and shutdown layers. The startup sequence is defensively structured: the validation pipeline routes safety/integrity failures through unconditional FATAL paths (ADR-004), MCP subprocess startup fails closed with a single retry-once, the `HttpStartupError`→`RuntimeError` hierarchy means the retry applylist captures the real startup failure, the httpx client has a leak-window cleanup before `ctx.services` is assigned and is always closed in the session `finally`, and the shutdown coordinator orders WAL checkpoint-before-cancellation with concurrent service shutdown.
- Highest-risk area: **MCP subprocess startup and its retry/shutdown boundary** (`McpServerStarter.start_servers`/`verify_health` + `HttpServerLifecycleManager.start` + `_ServerLifecycleRouter`). Scrutinized for retry gaps, orphaned subprocesses, shutdown-during-startup races, and resource leaks; none found.
- Recommended next step: **proceed.** No fix required. The items below are all Low/Informational; each is either intentional separation, a deliberate fail-closed tradeoff, or defensive fragility that is currently safe. None warrants a tracked issue.

## Adversarial scenarios exercised

| Scenario | Path examined | Outcome |
|---|---|---|
| MCP subprocess exits during health poll | `HttpServerLifecycleManager.start` + `_health_poll_until_ready` | `HttpStartupError` (a `RuntimeError`); caught by retry tuple, retried once, then fail-closed. |
| Shutdown requested during a startup stage | `StartupOrchestrator._run_stage` + `_raise_if_shutdown_requested` | Stage task cancelled and awaited; `StartupInterrupted` raised; `run()` rolls back started servers. |
| Init fails before `ctx.services` assigned | `ComponentInitializer.initialize` `except BaseException` + `_cleanup_on_failure` | Exposed httpx client `aclose()`d; original exception re-raised unchanged. |
| `git checkout`/subprocess start while shutting down | `_ServerLifecycleRouter.start_http_subprocess` `_shutting_down` guard | `StartSuppressedError`; no new subprocess spawned. |
| Cooldown throttle on repeated failed start | `_ServerLifecycleRouter._in_cooldown` / `ensure_ready` | `ServerCooldownError` throttles automatic restart only; explicit `start_http_subprocess` is not throttled. |
| RAG consistency check hangs | `check_services` `asyncio.wait_for` + `stop.set()` on `TimeoutError` | Times out to a WARNING; startup continues with RAG unverified (fail-closed downstream). |
| Missing `auth_token` on an MCP server | `check_config` `missing_auth` | Single FATAL under `mcp_auth`; startup aborts before spawning. |
| Unexpected exception during readiness probe | `check_services` `except Exception` on `collect_server_postures` | Captured as a `readiness` FATAL, not a crash. |
| Normal exit / interrupt after startup | `repl.py run()` `finally` → `close_resources` | `svc.http.aclose()` + `lifecycle.shutdown_all()` run on every exit path. |
| `HttpStartupError` outside the retry tuple? | `http_lifecycle_errors.HttpStartupError(RuntimeError)` | Impossible — it is a `RuntimeError`, so the tuple always covers it. |

## Findings

No Medium-or-higher finding survived adversarial scrutiny. The three items below are all Low/Informational; each is either intentional separation, a deliberate fail-closed tradeoff, or defensive fragility that is currently safe. None warrants a tracked issue.

### F-001 — `StartupOrchestrator` adds one pass-through level per startup stage

- Title: Thin delegation wrappers around each startup stage.
- Severity: Low
- Confidence: High
- Evidence label: Observed
- Evidence: `startup.py` `StartupOrchestrator._start_servers` → `self._mcp_starter.start_servers()`, `_verify_mcp_health` → `self._mcp_starter.verify_health()`, `_setup_prompt` → `self._prompt_setup.setup_prompt()`; `_check_config`/`_check_services` delegate to `StartupValidationPipeline` via `_finish_validation_stage`.
- Current behavior: Each stage method is a near-pure pass-through to a focused class (`McpServerStarter`, `PromptSetup`, `StartupValidationPipeline`). The wrappers exist mainly to host the `_raise_if_shutdown_requested` boundary checks between stages.
- Impact: Real but low — this is unnecessary indirection (a maintainability/cost concern), not a defect. The delegation does give named stage boundaries for shutdown checks, which is why it exists.
- Recommended action: None required. If the pass-throughs are ever collapsed, preserve the shutdown-boundary interleaving. This is the primary *refactoring consideration* for the startup layer: the five delegating methods could be inlined into `run()` if the stage-boundary shutdown checks are moved into `_run_stage`/a shared helper — but that is a behavior-preserving structural change, out of scope for a review.

### F-002 — RAG consistency worker thread is not joined on the timeout path

- Title: Executor worker outlives the timeout bound.
- Severity: Informational
- Confidence: High
- Evidence label: Observed
- Evidence: `startup_validation.py::check_services` runs `RagMaintenanceService().consistency(stop=stop)` via `asyncio.run_in_executor(None, ...)` wrapped in `asyncio.wait_for(..., timeout=RAG_CONSISTENCY_TIMEOUT_SEC)`.
- Current behavior: On `TimeoutError` (and on `CancelledError`), `stop.set()` signals the worker to stop, but the executor future/thread is not awaited or joined after cancellation, so the worker thread may keep running until it next observes `stop`.
- Impact: Low — a lingering background thread on the rare timeout/cancel path; Python eventually reclaims it. Inherent to the `run_in_executor` + `wait_for` pattern; not fixable without restructuring the RAG check into an awaitable or joining the worker.
- Recommended action: None unless RAG-check timeouts become a measured concern.

### F-003 — Retry-once relies on an explicit exception allowlist

- Title: `start_servers` retry depends on a fixed exception tuple.
- Severity: Informational
- Confidence: High
- Evidence label: Verified
- Evidence: `startup_mcp_starter.py::start_servers` wraps the first attempt in `except (OSError, RuntimeError, TimeoutError, ConnectionRefusedError, ConnectionResetError, BrokenPipeError)`; `http_lifecycle_errors.HttpStartupError(RuntimeError)`.
- Current behavior: The real startup-failure type `HttpStartupError` is a `RuntimeError`, so it is always caught and retried once; a second failure fails closed. Correct today.
- Impact: Currently safe. The protection is an allowlist rather than a guarantee: any future exception type raised by `_start_http_subprocess_once` outside the tuple would skip the retry and abort the whole startup loop mid-iteration (fail-closed, but without the once-retry). 
- Recommended action: Optional hardening — catch `Exception` at the outer boundary and route non-retriable types through, or document that the tuple is the complete set of transient startup failures.

## Refactoring considerations (not findings)

- **Pass-through layer (F-001):** the five delegating `StartupOrchestrator` methods are thin wrappers. Collapsing them into `run()` is a behavior-preserving refactor; preserve the `_raise_if_shutdown_requested` stage boundaries regardless of layout.
- **Duplicate lazy import:** `from agent.startup import StartupInterrupted` appears four times inside `startup_mcp_starter.py` method bodies. This is **intentional and safe** — `startup.py` imports `McpServerStarter` at module level, so a module-top import here would create a circular import. The lazy imports avoid the cycle. Do not "clean up" to a top-level import without breaking startup import.

## Open Questions

- Question: Is F-001's pass-through layer worth collapsing as a maintenance refactor?
- Why it matters: It is the only maintainability observation in the startup layer. Collapsing it is low-risk (behavior-preserving) but touches the central orchestration method.
- Required confirmation: Confirm whether the stage-boundary shutdown checks justify the wrappers as-is. If they are deemed pure noise, inline them into `run()` while preserving the `_raise_if_shutdown_requested` calls.

## Suggested Tests

- Test target: `McpServerStarter.start_servers` when `_start_http_subprocess_once` raises `HttpStartupError` twice in a row.
- Behavior to verify: The first failure is caught, one retry is applied after `RETRY_DELAY_SEC`, and the second failure fails closed with a runtime error naming the server.
- Failure mode: A future edit that narrows the retry tuple (e.g. drops `RuntimeError`) would let `HttpStartupError` escape without the once-retry, changing the startup-failure UX.

## Documentation Notes

- Target document: the ADR-004 fail-fast / FATAL-routing contract referenced in `startup.py` and `startup_validation.py`, and the `scripts/agent/` guarded reference table.
- Required update: none. The posture/validation behavior matches the documented ADR-004 decision and the reference table shows no drift.

## Final Recommendation

**Proceed.** No Medium-or-higher finding survives adversarial scrutiny. The toolchain is green (ruff, mypy clean over 9 modules; bandit only documented B404 `subprocess` notes; `generate_reference_table --check` clean; 593 startup-adjacent tests pass). The three Low/Informational items are intentional separation, a defensive-fragility note, or by-design audit behavior; none is actionable enough to warrant a tracked issue. The single Open Question (F-001 pass-through collapse) is confirmable without code change and does not block.
