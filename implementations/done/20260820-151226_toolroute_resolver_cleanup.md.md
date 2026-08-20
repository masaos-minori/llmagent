# Implementation Procedure: Remove legacy backward-compatibility arguments and unreachable diagnostic path from ToolRouteResolver

## Goal
Remove the unread `server_configs`, `discovery_map`, and `known_tools` parameters (and the `_log_routing_coverage()` diagnostic method they exist to support) from `ToolRouteResolver.__init__`, and update the sole production caller (`ToolExecutor.__init__`) and all test call sites to the new, smaller constructor signature — with no change to runtime routing behavior.

## Goal
Remove the unread `server_configs`, `discovery_map`, and `known_tools` parameters (and the `_log_routing_coverage()` diagnostic method they exist to support) from `ToolRouteResolver.__init__`, and update the sole production caller (`ToolExecutor.__init__`) and all test call sites to the new, smaller constructor signature — with no change to runtime routing behavior.

## Scope
- Target files:
  - `scripts/shared/route_resolver.py`: remove `server_configs`, `discovery_map`, `known_tools` params; remove `self._discovery_map`; remove `_log_routing_coverage()`; update docstrings
  - `scripts/shared/tool_executor.py`: update the `ToolRouteResolver(...)` call; remove `discovery_map` parameter from `ToolExecutor.__init__`; keep `server_configs`/`self._server_configs` (used by `_check_startup_mode()`)
  - Test files:
    - `tests/shared/test_route_resolver.py`: remove/rewrite `TestDiscoveryMap...` tests and `TestLogRoutingCoverage`; keep other tests with updated constructor calls
    - `tests/agent/services/test_runtime_tool_routing_integration.py`: delete `TestLogRoutingCoverageWithRuntime`; update `ToolRouteResolver` calls
    - `tests/shared/test_rag_tools_consistency.py`: drop `discovery_map=None`
    - `tests/docs/test_github_config_consistency.py`: update `ToolRouteResolver(server_configs={})` call
    - `tests/integration/test_agent_mcp_integration.py`: drop `discovery_map={_HTTP_TOOL: _HTTP_KEY}`
    - `tests/integration/test_rag_turn_integration.py`: drop `discovery_map={name: _HTTP_KEY for name in tool_names}`
    - Add regression test confirming `ToolRouteResolver(runtime_registry=...)` resolves correctly

## Assumptions
- No other caller outside `scripts/` and `tests/` constructs `ToolRouteResolver` or passes `discovery_map=` to `ToolExecutor`
- `ToolExecutor.__init__`'s `server_configs` parameter and `self._server_configs` attribute are preserved (used by `_check_startup_mode()`)
- The two integration-test helpers that pass `discovery_map=` to `ToolExecutor` immediately monkey-patch `executor._resolver.resolve = lambda _: _HTTP_KEY` right after construction — so dropping the `discovery_map=...` kwarg is safe
- No behavior change to `resolve()` or `RuntimeToolRegistry`-based routing

## Design decisions
- `ToolRouteResolver.__init__` new signature:
  ```python
  def __init__(self, *, warn_on_missing: bool = False, strict_mode: bool = False, runtime_registry: RuntimeToolRegistry | None = None) -> None:
  ```
  All keyword-only, matching what `resolve()` actually consults
- `ToolExecutor.__init__` keeps `server_configs` but drops `discovery_map`; its `ToolRouteResolver(...)` call becomes `ToolRouteResolver(warn_on_missing=..., strict_mode=...)` with current defaults
- Docstring updates: drop all references to `server_configs`, `discovery_map`, `known_tools`, `_log_routing_coverage()`
- Test rewrites: delete `TestDiscoveryMap...` and `TestLogRoutingCoverage` classes entirely (they test only the removed surface); update remaining `ToolRouteResolver(...)` calls; add regression test for `ToolRouteResolver(runtime_registry=...)`

## Implementation steps

### Phase 1: Source changes
1. Edit `scripts/shared/route_resolver.py`:
   - Remove `server_configs`, `discovery_map`, `known_tools` params from `__init__`
   - Remove `self._discovery_map`
   - Delete `_log_routing_coverage()` method
   - Update `__init__` and class docstrings

2. Edit `scripts/shared/tool_executor.py`:
   - Remove `discovery_map` param from `ToolExecutor.__init__`
   - Update `ToolRouteResolver(...)` call site (lines 72-74) to new signature

3. Run `uv run python -m compileall -q scripts/` to confirm no syntax breakage

### Phase 2: Test updates
1. `tests/shared/test_route_resolver.py`: delete `TestDiscoveryMap...` tests and `TestLogRoutingCoverage`; update remaining `ToolRouteResolver(...)` calls
2. `tests/agent/services/test_runtime_tool_routing_integration.py`: delete `TestLogRoutingCoverageWithRuntime`; update remaining calls
3. `tests/shared/test_rag_tools_consistency.py`: drop `discovery_map=None` from construction call
4. `tests/docs/test_github_config_consistency.py`: update `ToolRouteResolver(server_configs={})` call to drop the arg
5. `tests/integration/test_agent_mcp_integration.py`: drop `discovery_map={_HTTP_TOOL: _HTTP_KEY}` from `ToolExecutor(...)` call
6. `tests/integration/test_rag_turn_integration.py`: drop `discovery_map={name: _HTTP_KEY for name in tool_names}` from `ToolExecutor(...)` call
7. Add regression test in `tests/shared/test_route_resolver.py` confirming `ToolRouteResolver(runtime_registry=...)` resolves correctly
7. Add regression test in `tests/shared/test_tool_executor.py` confirming `_check_startup_mode()` still returns disabled-server error for `startup_mode == StartupMode.NONE`

### Phase 3: Full-repo re-grep and validation
1. Re-run `grep -rn "ToolRouteResolver("` and `grep -rn "discovery_map=\|known_tools=\|_log_routing_coverage"` across `scripts/` and `tests/` — confirm zero hits for removed surface
2. Run standard validation sequence per `rules/toolchain.md` (ruff, mypy, lint-imports, bandit, targeted + full pytest, diff-cover, pre-commit)
3. No `deploy/deploy.sh` change needed

## Validation plan
- `uv run pytest tests/shared/test_route_resolver.py -v` — all pass; no reference to removed args/method
- `uv run pytest tests/shared/test_tool_executor.py -v` — `_check_startup_mode()` behavior unchanged
- `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -v` — RuntimeToolRegistry-based resolution, strict_mode, warn_on_missing still covered
- `uv run pytest tests/shared/test_rag_tools_consistency.py -v` — RAG tools still resolve
- `uv run pytest tests/docs/test_github_config_consistency.py -v` — `tool_names` still validated
- `uv run pytest tests/integration/test_agent_mcp_integration.py tests/integration/test_rag_turn_integration.py -v` — `ToolExecutor` construction without `discovery_map` succeeds
- Repo-wide surface check: `grep -rn "ToolRouteResolver(" scripts/ tests/` — zero hits for removed args; `grep -rn "_log_routing_coverage" scripts/ tests/` — zero hits
- Full suite: `uv run pytest` — no new failures
- Lint/type/arch/security: `uv run ruff check scripts/`, `uv run mypy scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml`
- Coverage: `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` — ≥90% on changed lines
- Pre-commit: `uv run pre-commit run --all-files` — passes

## Traceability
- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/done/20260818-223204_require.md
- Source plan: plans/20260819-181912_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-151226
- Related target files: scripts/shared/route_resolver.py, scripts/shared/tool_executor.py, tests/shared/test_route_resolver.py, tests/agent/services/test_runtime_tool_routing_integration.py, tests/shared/test_rag_tools_consistency.py, tests/docs/test_github_config_consistency.py, tests/integration/test_agent_mcp_integration.py, tests/integration/test_rag_turn_integration.py