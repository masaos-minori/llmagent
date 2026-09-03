# Implementation Procedure: scripts/agent/startup.py

## Goal

Reduce `StartupOrchestrator` from 668 lines to a thin sequencer by delegating eight concerns to extracted modules/classes, while preserving all public contracts, rollback behavior, log messages, and output text.

## Scope

- Replace method bodies in `StartupOrchestrator` with delegation calls to six extracted components plus one shared helper
- Preserve `__init__(ctx, view, shutdown_event)` signature exactly
- Preserve `run() -> tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]` return type exactly
- Preserve rollback-on-failure `shutdown_all()` behavior in `run()`'s exception handler
- Preserve startup sequence order: `_initialize` → `_start_servers` → `_verify_mcp_health` → `_check_services` → `_recover_pending_approvals` → `_setup_prompt`
- Preserve fatal-vs-warning classification (production-profile MCP subprocess start failures raise `RuntimeError`, non-production only warn)
- Preserve `StartupInterrupted` exception raise conditions and `shutdown_event`-racing behavior
- Preserve all log message strings and `_view.write_*` output text

## Assumptions

- The constructor-injection/delegation pattern used in `orchestrator.py` and `ingester.py` splits is acceptable as a reference
- The six concern groupings listed under Implementation Intent are reasonable boundaries
- The consolidated retry-once-with-delay helper serves only this file's two call sites (scoped narrowly per Plan assumption)
- The consolidated per-source counting helper should be parameterized by source name and return OK/FATAL/WARNING/SKIPPED counts
- All six extracted modules will be imported inside `StartupOrchestrator` methods (lazy import) rather than at module level to avoid circular imports

## Design decisions

- **Lazy imports over module-level**: Import each extracted component inside the method body where needed, matching the existing pattern (`from agent.commands.registry import CommandRegistry` inside `_init_command_registry`). This avoids circular dependency risk between `startup_component_init.py`, `startup_mcp_starter.py`, etc.
- **Component instances stored as instance attributes**: Each delegated component is instantiated once in `__init__` and stored as `self._component_*` attribute, consistent with how `StartupOrchestrator` currently stores `_cmds`, `_orchestrator`, `_spawned_subprocesses`.
- **Shared helper as module-level function**: `retry_helper.py` exports a single `retry_once_with_delay()` function (not a class) because it has no state and is called from two different methods.
- **Per-source counting helper as module-level function**: `startup_reporter.py` exports a `_count_by_status(pipeline, source)` helper that returns an ordered dict `{OK: n, FATAL: n, WARNING: n, SKIPPED: n}` for a given source.
- **No new public APIs**: All extracted components expose only private methods (`_method`) matching the current `StartupOrchestrator` method names they replace.

## Alternatives considered

- **Single-class approach**: Keep one `StartupOrchestrator` class but move methods to separate modules via inheritance. Rejected: inheritance adds complexity without solving the same-file review problem.
- **Factory pattern**: Create a factory that builds `StartupOrchestrator` with injected dependencies. Rejected: adds indirection; constructor injection already used elsewhere in the codebase.
- **Protocol-based interfaces**: Define `Protocol` types for each component interface. Rejected: premature abstraction; concrete classes are sufficient for this refactor.

## Implementation

### Target file

`scripts/agent/startup.py`

### Procedure

Replace all eight concern method bodies with delegation calls to extracted components. Remove duplicated retry logic. Replace per-source counting blocks with shared helper call.

### Method

Modify existing class — no new methods added.

### Details

**Phase 3: Reduce StartupOrchestrator** (REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013)

1. **`__init__` changes**: Add instantiation of six component classes as instance attributes. No signature change.

```python
def __init__(
    self,
    ctx: AgentContext,
    view: CLIView,
    shutdown_event: asyncio.Event | None = None,
) -> None:
    self._ctx = ctx
    self._view = view
    self._cmds: CommandRegistry | None = None
    self._orchestrator: Orchestrator | None = None
    self._spawned_subprocesses: list[subprocess.Popen] = []
    self._shutdown_event = shutdown_event
    # Delegated components
    self._component_init = ComponentInitializer(ctx, view)
    self._mcp_starter = McpServerStarter(ctx, view, shutdown_event)
    self._validation_pipeline = StartupValidationPipeline(ctx, view)
    self._reporter = ReadinessReporter(ctx, view)
    self._approval_recovery = ApprovalRecovery(ctx, view)
    self._prompt_setup = PromptSetup(ctx, view)
```

2. **`run` method**: No structural change. Sequence order preserved. Rollback-on-failure preserved. Only change: method bodies below are replaced with delegation calls.

3. **`_initialize`**: Replace body with single delegation call.

```python
async def _initialize(self) -> None:
    """Setup readline, wire DI, init CommandRegistry and Orchestrator."""
    self._component_init.initialize()
```

4. **`_start_servers`**: Replace body with delegation call. Duplicated retry logic removed (moved to `McpServerStarter`).

```python
async def _start_servers(self) -> list[subprocess.Popen]:
    """Spawn subprocesses for HTTP subprocess MCP servers."""
    return await self._mcp_starter.start_servers()
```

5. **`_verify_mcp_health`**: Replace body with delegation call. Duplicated retry logic removed.

```python
async def _verify_mcp_health(self) -> None:
    """Verify health of all MCP subprocess servers after startup."""
    await self._mcp_starter.verify_health()
```

6. **`_check_services`**: Replace body with delegation call. Per-source counting replaced with shared helper call inside `ReadinessReporter`.

```python
async def _check_services(self) -> None:
    """Probe LLM/Embed health, validate tool definitions, and audit security defaults."""
    pipeline = await self._validation_pipeline.check_services()
    self._reporter.report_readiness(pipeline)
```

7. **`_recover_pending_approvals`**: Replace body with delegation call.

```python
async def _recover_pending_approvals(self) -> None:
    """Restore workflow approval-pending state from a previous session."""
    await self._approval_recovery.recover()
```

8. **`_setup_prompt`**: Replace body with delegation call.

```python
async def _setup_prompt(self) -> None:
    """Inject semantic memories into the initial system prompt."""
    await self._prompt_setup.setup()
```

9. **Remove these methods entirely** (their logic moved to extracted components):
   - `_interruptible_sleep` (moved to `McpServerStarter`)
   - `_start_http_subprocess_once` (moved to `McpServerStarter`)
   - `_display_pipeline_results` (moved to `ReadinessReporter`)
   - `_report_readiness` (replaced by shared helper inside `ReadinessReporter`)
   - `_classify_memory_failure` (moved to `PromptSetup`)

10. **Remove module-level constant** `HEALTH_CHECK_RETRY_DELAY_SEC` (consolidated into `retry_helper.py`).

11. **Update imports**: Remove imports that are no longer needed at module level (e.g., `httpx`, `time` may still be needed if used elsewhere). Keep imports required by remaining module-level code.

## Compatibility considerations

- **Critical**: `scripts/agent/repl.py` must continue to instantiate `StartupOrchestrator(ctx, view, shutdown_event)` and call `.run()` with identical return type. Any signature or contract change breaks the consumer.
- **Rollback semantics**: `run()`'s `except Exception as setup_err:` block must still call `await self._ctx.services_required.lifecycle.shutdown_all()` before re-raising. This is the only rollback path.
- **Exception types**: `StartupInterrupted` must still be raised when `shutdown_event` fires during sleep/delay. `RuntimeError` must still be raised on production-profile MCP failure.
- **Log messages**: Every `logger.info/warning/error` string must remain byte-for-byte identical.
- **Output text**: Every `_view.write_*` call must produce identical text output.

## Security considerations

- Production vs. non-production error handling must remain distinct: production raises `RuntimeError` on MCP failure, non-production logs warning.
- `_mask_secrets` must still be applied to error messages before logging/display.
- `StartupInterrupted` must not leak sensitive information through its message.

## Rollback considerations

- If any delegation breaks behavior, revert to original 668-line file. The original file is preserved in git history.
- If `retry_helper.py` introduces regression in retry logic, revert to inline retry patterns in `_start_servers` and `_verify_mcp_health`.
- If per-source counting helper breaks `_report_readiness()` output format, revert to five repeated counting blocks.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| `scripts/agent/startup.py` | Unit — verify delegated methods produce identical output | `uv run pytest tests/agent/test_startup.py` | No new failures |
| `scripts/agent/repl.py` | Integration — consumer compatibility | `uv run pytest tests/agent/test_repl.py` | No new failures |
| All new files | lint/type/security | `ruff check`, `mypy`, `bandit` | Clean |
| Full suite | Regression baseline comparison | `uv run pytest` | No new failures vs. pre-change baseline |

## Completion criteria

- [ ] `StartupOrchestrator.__init__` signature unchanged: `(ctx, view, shutdown_event)`
- [ ] `StartupOrchestrator.run()` return type unchanged: `tuple[CommandRegistry, Orchestrator, list[subprocess.Popen]]`
- [ ] All eight concern method bodies replaced with delegation calls (no orphaned logic)
- [ ] Removed methods: `_interruptible_sleep`, `_start_http_subprocess_once`, `_display_pipeline_results`, `_report_readiness`, `_classify_memory_failure`
- [ ] Module-level `HEALTH_CHECK_RETRY_DELAY_SEC` removed
- [ ] `StartupInterrupted` raise conditions preserved
- [ ] Fatal-vs-warning classification preserved
- [ ] All log message strings identical to pre-change
- [ ] All `_view.write_*` output text identical to pre-change
- [ ] `scripts/agent/repl.py` works unmodified against refactored `StartupOrchestrator`
- [ ] `ruff`, `mypy`, `bandit` clean on modified file
- [ ] All four test files pass unchanged in outcome

## Out of scope

- Changing startup sequence order
- Changing timeout/retry values
- Adding new validation checks
- Modifying `scripts/agent/repl.py`, `scripts/agent/repl_health.py`, `scripts/agent/http_lifecycle.py`, or `scripts/agent/factory.py` internals
- Performance optimization
- New public API additions to `StartupOrchestrator`

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
- **Requirement ID**: REQ-007, REQ-008, REQ-009, REQ-010, REQ-011, REQ-012, REQ-013
- **Source issue**: issues/20260831-155933_refactor_008_startup_separation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-073153_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-142637
- **Related target files**: scripts/agent/startup.py
