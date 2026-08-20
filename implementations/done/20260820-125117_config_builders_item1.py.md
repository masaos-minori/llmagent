# Implementation Procedure: Wire agent_memory_max_startup_snippets in config_builders.py (Item 1)

## Goal
Wire `agent_memory_max_startup_snippets` into the toml build path (`config_builders.py`) so it is genuinely configurable end to end.

## Scope
- Target file: `scripts/agent/config_builders.py`
- Add `_get_int_or_default(cfg, "agent_memory_max_startup_snippets", 10)` in `build_agent_config`
- Pass it into the `AgentConfig(...)` constructor call

## Assumptions
- `agent_memory_max_startup_snippets` already exists on `AgentConfig` (line 434 in config_dataclasses.py)
- `startup.py:637` already reads `ctx.cfg.agent_memory_max_startup_snippets` - once wired, this becomes genuinely configurable
- No validation needed at `AgentConfig` level (consistent with other `AgentConfig`-level scalars)

## Design decisions
- Mirror how every other `AgentConfig`-level scalar (e.g. `otel_enabled`, `structured_log`) is built
- Add local variable before `return AgentConfig(...)` statement
- Use default value 10 (matching dataclass default)

## Implementation
### Target file
`scripts/agent/config_builders.py`

### Procedure
1. In `build_agent_config()` function, add wiring for `agent_memory_max_startup_snippets`
2. Pass it into the `AgentConfig(...)` constructor

### Method
Direct code modification using exact line matching

### Details
**Location:** In `build_agent_config()` function, around line 478-497 (the `return AgentConfig(...)` block)

**Add before the `return AgentConfig(...)` (after line 495 `diagnostics=_build_diagnostics_config(cfg),`):**
```python
    agent_memory_max_startup_snippets=_get_int_or_default(
        cfg, "agent_memory_max_startup_snippets", 10
    ),
```

**The AgentConfig constructor call should include this new parameter (around line 496):**
```python
    return AgentConfig(
        llm=_build_llm_config(cfg),
        rag=_build_rag_config(cfg),
        tool=_build_tool_config(cfg, system_prompt_tool),
        memory=_build_memory_config(cfg),
        mcp=MCPConfig(
            mcp_servers=_build_mcp_servers(cfg),
            security_profile=security_profile_val,
            security_lockdown_enabled=security_lockdown_enabled,
        ),
        approval=_build_approval_config(cfg),
        obs=ObservabilityConfig(
            otel_enabled=otel_enabled,
            otel_endpoint=_get_str_or_default(cfg, "otel_endpoint", ""),
            otel_service_name=_get_str(cfg, "otel_service_name") or "llm-agent",
            audit_log_file=_get_str(cfg, "audit_log_file") or "/opt/llm/logs/audit.log",
            structured_log=structured_log,
        ),
        diagnostics=_build_diagnostics_config(cfg),
        agent_memory_max_startup_snippets=_get_int_or_default(
            cfg, "agent_memory_max_startup_snippets", 10
        ),
    )
```

## Compatibility considerations
- No behavior change for operators who don't set this key (default 10 preserved)
- Operators who already set this key in toml will now have it take effect
- No dataclass change needed - field already exists on `AgentConfig`

## Security considerations
- None - config wiring only

## Rollback considerations
- Git revert of this file if issues arise

## Validation plan
- Run `uv run pytest tests/agent/test_config_builders.py -v` - all pass including new behavior
- Add build-path test confirming non-default toml value reaches `AgentConfig.agent_memory_max_startup_snippets` (separate test procedure)

## Out of scope
- Tests (separate procedure)
- `config_reload.py` changes (reuses `build_agent_config`)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-215146_require.md
- Source plan: plans/20260819-165438_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-125117
- Related target files: scripts/agent/config_builders.py