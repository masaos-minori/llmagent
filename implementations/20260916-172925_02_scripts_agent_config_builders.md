## Goal

`build_agent_config()` — the earliest production-validation call site, invoked from `agent/context.py::AgentContext.__init__` before `StartupOrchestrator` runs — calls `ProductionConfigValidator().validate(cfg, security_profile=security_profile_val)` without a `known_tools` argument, relying entirely on the validator's internal best-effort fallback. Must resolve and pass the authoritative tool set explicitly. (REQ-002; AC-1)

## Scope

- In `build_agent_config()`, resolve the authoritative known-tool set via `shared.tool_registry.get_registry()` and pass it to `ProductionConfigValidator().validate(...)` instead of omitting `known_tools`.

## Assumptions

- The existing `config_builders.py` already imports `ProductionConfigValidator` at line 25.
- The existing `config_builders.py` already imports `SecurityProfile` at line 22 (used by `build_agent_config`).
- The existing `tool_registry.py`'s `get_registry()` function is available and callable.

## Design decisions

- Use the same registry resolution pattern as the existing `_resolve_known_tools()` function but capture the result explicitly rather than relying on the validator's internal fallback.
- Keep the change minimal — only add the registry call and pass the result as `known_tools`.

## Alternatives considered

- Adding a new `get_known_tools()` helper — unnecessary since the existing `_resolve_known_tools()` function already provides this pattern.
- Using a context manager for registry access — overkill for a simple singleton lookup.

## Compatibility considerations

- Existing callers passing `known_tools={...}` explicitly are unaffected — the fail-closed change applies only to the default/registry-resolution path.
- A caller passing `security_profile="production"` will now be coerced to `SecurityProfile.PRODUCTION` (no behavioral change since `"production"` maps to the same enum value).
- A caller passing `security_profile="local"` will now receive a validation error instead of being silently accepted.

## Security considerations

- Preventing silent skip-on-registry-failure eliminates the possibility of production validation succeeding without authoritative tool-set information.
- Rejecting unknown security-profile values prevents configuration drift where legacy profile names could bypass intended security enforcement.

## Rollback considerations

- Reverting the exception-handling change restores the pre-fix behavior where registry failures silently skip validation.
- Reverting the security-profile coercion removes the validation error for unsupported profile values.

## Implementation

### Target file

`scripts/agent/config_builders.py`

### Procedure

1. **Phase 1: Explicit known_tools injection**
   - In `build_agent_config()`, resolve the authoritative known-tool set via `shared.tool_registry.get_registry()` and pass it to `ProductionConfigValidator().validate(...)`.

### Method

- Edit `build_agent_config()` — add the registry call and pass the result as `known_tools`.

### Details

**Step 1 — Explicit known_tools injection:**

```python
# Before (line ~400):
results = ProductionConfigValidator().validate(
    cfg, security_profile=security_profile_val
)
```

```python
# After:
# REQ-002: resolve the authoritative known-tool set explicitly
try:
    from shared.tool_registry import get_registry
    known_tools = set(get_registry().get_all_tool_names())
except ValueError as exc:
    # Duplicate registration or other tool ownership conflict
    raise ConfigReloadValidationError(
        f"Tool registry resolution failed during config build: {exc}"
    ) from exc
except ImportError as exc:
    # Module import failure — registry module unavailable
    raise ConfigReloadValidationError(
        f"Tool registry module unavailable during config build: {exc}"
    ) from exc

results = ProductionConfigValidator().validate(
    cfg, security_profile=security_profile_val, known_tools=known_tools
)
```

## Validation plan

- Run unit tests: `uv run pytest tests/agent/test_config_builders.py tests/agent/test_startup.py -v`
- Verify no new failures; `known_tools` is resolved and passed explicitly.
- Static analysis: `uv run ruff check scripts/agent/config_builders.py`, `uv run mypy scripts/agent/config_builders.py`.

## Completion criteria

- [ ] `build_agent_config()` resolves `known_tools` explicitly via `get_registry()`.
- [ ] No new failures in `test_config_builders.py` or `test_startup.py`.
- [ ] No new lint/type/security errors introduced.

## Out of scope

- Modifying `scripts/mcp_servers/shell/` (the shell-mcp server's own `command_allowlist` check is a separate defense layer).
- Any MCP server business logic unrelated to the startup/discovery/registry-publication path.

## execution_status

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20260914-103115_mcpagent03_production-security-profiles-fail-closed-validation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-120933_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-172925
- **Related target files**: scripts/agent/config_builders.py
