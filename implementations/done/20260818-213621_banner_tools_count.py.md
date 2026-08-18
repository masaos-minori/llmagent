## Goal

Update the agent banner to report the number of tools available via the `RuntimeToolRegistry` instead of the static `tool_definitions` list, ensuring accurate representation of runtime capabilities.

## Scope

**In-Scope:**
- Modify `AgentREPL._n_tools` in `scripts/agent/repl.py` to query `RuntimeToolRegistry` for the current number of tools.
- Update any documentation describing the banner behavior.

**Out-of-Scope:**
- Changes to `RuntimeToolRegistry` itself (no new methods needed — `all_tools()` already exists).
- Changes to tool discovery logic.
- Changes to configuration loading.

## Assumptions

- `RuntimeToolRegistry.all_tools()` returns only tools from non-excluded servers (`_is_excluded_server()` filters out unavailable/degraded servers during construction at `runtime_tool_registry.py:62-64`).
- The banner display context has access to the `RuntimeToolRegistry` instance (verify how `AgentContext` stores the registry reference).
- No new methods are needed on `RuntimeToolRegistry` — `len(registry.all_tools())` suffices (check if adding a `__len__` method would be cleaner).

## Findings

### Claim: Update `_n_tools` to use `RuntimeToolRegistry`

**Status: VALID — IMPLEMENTED**

`RuntimeToolRegistry` exists and provides `all_tools()` method. `AppServices` has `runtime_tools: RuntimeToolRegistry | None` attribute. Access path confirmed: `self._ctx.services.runtime_tools`.

Changes made:
- Updated `_n_tools` property in `scripts/agent/repl.py` to query `RuntimeToolRegistry.all_tools()` instead of static `tool_definitions`
- Added null-safety check (`rt.all_tools() if rt else 0`)
- Updated docstring to clarify runtime semantics

### Optional: Add `__len__` to `RuntimeToolRegistry`

**Status: NOT TAKEN**

Not needed — `len(registry.all_tools())` is clear enough and avoids unnecessary coupling.

## Implementation

### Part A: Update `_n_tools` property

**Status: COMPLETE**

Changes made in `scripts/agent/repl.py`:

```python
# BEFORE:
@property
def _n_tools(self) -> int:
    """Number of tools available (from config/tools_definitions.toml)."""
    return len(self._ctx.cfg.tool.tool_definitions)

# AFTER:
@property
def _n_tools(self) -> int:
    """Number of tools available at runtime (excludes unavailable/degraded servers)."""
    rt = self._ctx.services_required.runtime_tools
    return len(rt.all_tools()) if rt else 0
```

- Uses `services_required` to ensure services are initialized before accessing `runtime_tools`
- Null-safety: returns 0 when `runtime_tools` is None
- No import changes needed — `services_required` already accessible via `self._ctx`

## Compatibility considerations

- Changing `_n_tools` to use `RuntimeToolRegistry` is backward compatible — the property name and return type remain the same.
- Adding `__len__` to `RuntimeToolRegistry` is backward compatible — Python allows both `len(obj)` and `for x in obj` simultaneously.
- Documentation updates do not affect runtime behavior.

## Security considerations

- N/A — no new secrets, keys, or sensitive data introduced.
- No changes to authentication, authorization, or data access patterns.

## Rollback considerations

- Revert `_n_tools` change: restore original implementation using `self._ctx.cfg.tool.tool_definitions`.
- Revert `__len__` addition to `RuntimeToolRegistry`: remove the method.
- Revert documentation updates: restore original text.
- No schema changes — rollback is purely code-level.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/agent/repl.py | Unit: verify banner count updates when tools are added/removed | Manual verification + `uv run pytest tests/agent/test_repl*.py -v` | All pass |
| scripts/agent/repl.py | Static type check | `uv run pyright scripts/agent/repl.py` | 0 errors |
| Repo-wide | Architecture boundary | `PYTHONPATH=scripts uv run lint-imports` | Contracts kept, 0 broken |

## Out of scope

- Sign-off gate enforcement (manual step before implementation).
- Deployment steps (Phase 3 of the plan).
- Documentation updates beyond docstring notes and inline comments.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: issues/20260817_08_issue.md
- Source requirement: requires/20260818-171300_require.md
- Source plan: plans/20260818-183638_plan.md
- Source implementation procedure: N/A
- Generated at: 20260818-213621
- Related target files: scripts/agent/repl.py, scripts/shared/route_resolver.py
