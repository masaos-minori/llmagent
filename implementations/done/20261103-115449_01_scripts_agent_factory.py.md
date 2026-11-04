## Goal

Give `build_agent_context` an optional keyword-only client-created hook that is invoked
with the fresh `httpx.AsyncClient` immediately after it is constructed and before
`LLMClient` or any later builder runs, so the async caller can reach the client during the
window before `ctx.services` is assigned (REQ-001; AC-001, AC-005). With the hook omitted,
behavior, builder order, and assignment timing are unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

Covers the `scripts/agent/factory.py` row (seq 01) and its companion test row
`tests/agent/test_agent_factory.py` (seq 03, companion-eligible, no document of its own)
of `plans/20261101-144316_factorycleanup001_factory-leaks-client-on-build-failure.md`.
Execution order for the plan: this document first (it declares the hook parameter the
seq 02 initializer consumes), then seq 02, then the plan-wide validation.

## Assumptions
- Verified against current source (20261103): `_build_llm_client` (factory.py:82)
  constructs `http = httpx.AsyncClient(timeout=ctx.cfg.llm.http_timeout)` at 95, followed
  directly by the `LLMClient(...)` call (96-108); `build_agent_context` (323) is a plain
  synchronous `def`, calls `_build_audit_logger`, `_build_llm_client`,
  `_build_tool_executor`, `_build_history_manager`, `_build_memory_services` in that order
  (330-335), and assigns `ctx.services = AppServices(...)` last (337-351). `Callable` is
  already imported from `collections.abc` (18); no `await` exists in the module.
- `AppServices.__init__` (context.py:290) enforces the non-`None` invariant for
  `http`/`llm`/`tools`/`lifecycle`/`hist_mgr`/`audit_logger` — a failing invariant check
  raises after all builders ran, inside the same pre-assignment window.
- radon today: `_build_llm_client` A(1), `build_agent_context` A(1); the added hook-call
  branch keeps both at A(2) at most (rank A gate, Plan Design).
- `factory.py` is 11466 B (gate 20480 B) — ample headroom.
- Companion tests use the file's existing pattern: `_apply_patches(monkeypatch)` over
  `_FACTORY_PATCHES` (92-100, includes `agent.factory.httpx.AsyncClient`,
  `agent.factory.LLMClient`, `agent.factory.ToolExecutor`) and `_make_ctx` (37).
- Gated plan: the six unresolved startup issues named in the Plan's Dependencies section
  are not prerequisites per the Plan; this document proceeds with a `Gated:` note on each
  Pending row and scheduling is the owner's decision.

## Design decisions
- Parameter name `on_client_created` (new): keyword-only, type
  `Callable[[httpx.AsyncClient], None] | None = None` (the `Callable` import already
  exists), threaded unchanged from `build_agent_context` into `_build_llm_client` and
  called there between the client construction and the `LLMClient` call — the earliest
  point the client exists (Plan REQ-001 wording; Plan Design decision).
- Hook exceptions are not contained in the factory: the only production hook is the seq 02
  initializer's one-attribute-assignment lambda, which cannot fail; a raising injected hook
  propagates inside the same window and is covered by the seq 02 initializer cleanup
  (client already exposed before the call). Adding a try/except here would add a branch
  for an unreachable case.

## Alternatives considered
- Calling the hook in `build_agent_context` after `_build_llm_client` returns: rejected —
  REQ-001 (Frozen) requires the call before `LLMClient` is built, and the `LLMClient`
  construction is itself a fail point inside the window.
- Returning the client from the factory instead of a hook: rejected by the Plan (the
  factory's return type and assignment timing must stay unchanged, AC-005).

## Implementation
### Target file
`scripts/agent/factory.py`

### Procedure
1. Write the red companion tests (see Companion test files) and confirm they fail (the
   keyword does not exist yet).
2. Change `_build_llm_client`'s signature (82-84) to
   `def _build_llm_client(ctx: AgentContext, view: CLIView, *, on_client_created:
   Callable[[httpx.AsyncClient], None] | None = None) -> LlmClientResult:` (new keyword);
   between line 95 and the `LLMClient(` call add
   `if on_client_created is not None: on_client_created(http)`.
3. Change `build_agent_context`'s signature (323) to
   `def build_agent_context(ctx: AgentContext, view: CLIView, *, on_client_created:
   Callable[[httpx.AsyncClient], None] | None = None) -> None:` (new keyword) and pass it
   through at the `_build_llm_client(ctx, view)` call (331):
   `_build_llm_client(ctx, view, on_client_created=on_client_created)`. Extend the
   docstring with one sentence naming the hook's purpose (early client exposure for the
   async caller's failure cleanup).
4. Builder order, the `ctx.services` assignment, and the absence of `await`/`asyncio`
   stay untouched (AC-005).

### Method
One keyword-only parameter threaded through two signatures plus one two-line call
statement; no behavior change when the keyword is omitted.

### Details
- The hook call sits inside `_build_llm_client`, after the client exists and before any
  code that can fail (`LLMClient(...)` and all later builders).
- radon gate: `_build_llm_client` and `build_agent_context` stay rank A (A(2) ceiling).
- No new public symbol beyond the keyword itself (functions already public;
  `tools/generate_reference_table.py --check` should report no drift — the keyword is a
  parameter, not a new symbol; regenerate only if the checker reports drift).

### Companion test files
- `tests/agent/test_agent_factory.py` (companion of the `scripts/agent/factory.py` row;
  Plan `Implementation Target Files` seq 03 covered here per the companion rule)
  - Procedure: add tests to the existing `TestBuildAgentContext` class (114) using
    `_apply_patches(monkeypatch)`:
    (i) `test_hook_called_with_client_before_later_builders` (new): record call order by
    giving the patched `httpx.AsyncClient`, `LLMClient` and `ToolExecutor` mocks
    `side_effect` lambdas that append their name to a list; pass a `MagicMock` hook as
    `on_client_created` (new); assert the hook was called exactly once with the patched
    `httpx.AsyncClient` mock's created instance, and the recorded order shows the client
    before `LLMClient` before `ToolExecutor` (REQ-001, REQ-004; AC-001).
    (ii) `test_later_builder_failure_exposes_hooked_client` (new): same fixture with
    `ToolExecutor` side_effect `RuntimeError("builder failed")`; assert
    `build_agent_context(ctx, view, on_client_created=hook)` raises that error and the
    hook was already called once with the created client (REQ-004 observation wording per
    the Plan's 20261103 assumption) — the raised error reaches the caller and the client
    is reachable only through the recorded hook argument.
    (iii) hook-omitted regression: every existing `TestBuildAgentContext` test stays
    byte-identical and green (AC-001 second half, REQ-001 "with the hook omitted").
  - Validation: `uv run pytest tests/agent/test_agent_factory.py -q` — new tests red
    before Procedure 2-3, green after.

## Compatibility considerations
- The single production caller `startup_component_init.py:55` calls
  `build_agent_context(ctx, self._view)` positionally and is unaffected until seq 02 passes
  the keyword (REQ-001 default).
- `_FACTORY_PATCHES` patches factory dependencies, not `build_agent_context` itself
  (Plan Risks mitigation confirmed 20261103).
- No `docs/` change (Plan Documentation Impact N/A).

## Security considerations
N/A: no new input; the hook receives an internal client object and only the seq 02
initializer supplies one.

## Rollback considerations
- Single-file additive change plus tests; revert the commit restores today's signatures.

## Validation plan
1. `uv run pytest tests/agent/test_agent_factory.py -q` — new tests red before
   Procedure 2, green after Procedure 3 (Validation plan row 1).
2. Static: `uv run ruff check scripts/agent/factory.py tests/agent/test_agent_factory.py`,
   `uv run ruff format --check` on both, `uv run mypy scripts/agent/factory.py`.
3. Gates: `uv run radon cc scripts/agent/factory.py -s` (rank A kept), `uv run bandit -r
   scripts/agent/factory.py -c pyproject.toml` (no new finding), `uv run python
   tools/check_module_size.py` (11466 B, ample), `uv run lint-imports` (contracts kept).
4. The plan-wide validation sequence (`rules/toolchain.md`, diff-cover) runs once after
   both documents of this plan are executed.

## Completion criteria
- AC-001: with a hook supplied it is called exactly once with the created
  `httpx.AsyncClient` before `LLMClient`, `ToolExecutor`, `HistoryManager` or memory
  services are built; all existing `TestBuildAgentContext` tests pass unchanged.
- AC-005: no `await`/`asyncio` added to the factory; builder order and `ctx.services`
  assignment timing unchanged.

## Out of Scope
- Consuming the hook and awaiting `aclose()` (`scripts/agent/startup_component_init.py`,
  seq 02).
- `scripts/agent/startup.py`, `repl.py`, `resource_shutdown_coordinator.py` (Reference
  Files, read-only).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Write red companion tests, confirm they fail (Procedure 1; Companion test files) | Pending | — | — | Gated: issues/20261031-135544_interruptexit001_startup-interrupt-exits-traceback.md phase all; issues/20261031-135634_validorder001_config-validation-after-spawn.md phase all; issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md phase all; issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md phase all; issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md phase all; issues/20261031-135607_wfschema001_schema-preflight-creates-database.md phase all - prose gate per the Plan's Dependencies section; none is a prerequisite; owner schedules |
| 2 | Add the keyword to both signatures and the hook call in `_build_llm_client` (Procedure 2-4) | Pending | — | — | Gated: issues/20261031-135544_interruptexit001_startup-interrupt-exits-traceback.md phase all; issues/20261031-135634_validorder001_config-validation-after-spawn.md phase all; issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md phase all; issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md phase all; issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md phase all; issues/20261031-135607_wfschema001_schema-preflight-creates-database.md phase all - prose gate per the Plan's Dependencies section; none is a prerequisite; owner schedules |
| 3 | Run this document's checks (Validation plan 1-3) | Pending | — | — | Gated: issues/20261031-135544_interruptexit001_startup-interrupt-exits-traceback.md phase all; issues/20261031-135634_validorder001_config-validation-after-spawn.md phase all; issues/20261031-135416_mcporphan001_subprocess-orphaned-startup-interrupt.md phase all; issues/20261031-135448_startretry001_startup-retry-blocked-cooldown.md phase all; issues/20261031-135522_disabledauth001_disabled-server-auth-fatal.md phase all; issues/20261031-135607_wfschema001_schema-preflight-creates-database.md phase all - prose gate per the Plan's Dependencies section; none is a prerequisite; owner schedules |

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
- **Requirement ID**: REQ-001 (optional keyword-only hook called right after client
  creation, default unchanged, no `await` in the factory), REQ-004 (factory hook tests)
- **Source issue**: issues/20261003-180345_factorycleanup001_factory-leaks-client-on-build-failure.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261101-144316_factorycleanup001_factory-leaks-client-on-build-failure.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261103-115449
- **Related target files**: `scripts/agent/factory.py`, `tests/agent/test_agent_factory.py`
