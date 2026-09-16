## Goal

Add `cfg.startup_mode != StartupMode.NONE` to `agent.services.tool_validation._collect_server_tool_names()`'s per-server skip condition, so that a disabled (`StartupMode.NONE`) server is never probed during the static-vs-live tool-definition drift check. (REQ-001; "No network request is sent to a disabled server during discovery")

## Scope

- Modify `_collect_server_tool_names()`'s per-server loop to also check `cfg.startup_mode != StartupMode.NONE` alongside the existing `srv_cfg.transport == TransportType.HTTP and srv_cfg.url` condition.

## Assumptions

- `StartupMode.NONE` is defined in `scripts/shared/mcp_config.py` and `McpServerConfig.is_disabled` returns `True` when `startup_mode == StartupMode.NONE`.
- The `_check_tool_definitions()` caller in `startup_validation.py` does not need modification — it only calls `_collect_server_tool_names()` and processes its return values.

## Design decisions

- Use `cfg.is_disabled` as the single predicate, consistent with how other parts of the codebase derive "disabled" status. This avoids four independent re-derivations of "is this server disabled" drifting apart over time.
- Resolve UNK-01's classification choice: treat a disabled server the same as "not configured" (excluded from both `cfg_names`/`server_names` comparison sets), consistent with how `mcp_tool_discovery.py`'s own `discover_all()` treats it.

## Alternatives considered

- Adding a new `is_none_mode` property on `StartupMode` — unnecessary since `is_disabled` already covers this.
- Checking `cfg.startup_mode` directly instead of `cfg.is_disabled` — equivalent but less semantic; `is_disabled` is the established convention.

## Compatibility considerations

- Existing non-disabled servers are unaffected; the added `is_disabled` check only short-circuits the loop earlier for disabled servers.
- A disabled server excluded by this change will not appear in either `cfg_names` or `server_names` in `_check_tool_definitions()`, which is consistent with treating it as "not configured."

## Security considerations

- Blocking network requests to disabled servers prevents potential lateral movement via a disabled-but-resolvable MCP endpoint.

## Rollback considerations

- Reverting the `is_disabled` check restores the pre-fix behavior where disabled servers could be probed during the tool-definition drift check.

## Implementation

### Target file

`scripts/agent/services/tool_validation.py`

### Procedure

1. **Phase 1: Discovery-layer exclusion**
   - In `_collect_server_tool_names()`'s per-server loop, add `and not cfg.is_disabled` to the existing skip condition on line 75.
   - Current code: `if srv_cfg.transport == TransportType.HTTP:` followed by `if not srv_cfg.url: continue`
   - New code: `if srv_cfg.transport == TransportType.HTTP and not srv_cfg.is_disabled:`

### Method

- Edit `_collect_server_tool_names()` at line 74-77 — add `and not srv_cfg.is_disabled` to the transport check condition.

### Details

**Step 1 — `_collect_server_tool_names()` skip condition:**

```python
# Before (lines 74-77):
for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
    if srv_cfg.transport == TransportType.HTTP:
        if not srv_cfg.url:
            continue

# After:
for key, srv_cfg in ctx.cfg.mcp.mcp_servers.items():
    if srv_cfg.transport == TransportType.HTTP and not srv_cfg.is_disabled:
        if not srv_cfg.url:
            continue
```

## Validation plan

- Run unit tests: `uv run pytest tests/agent/test_startup*.py -v`
- Verify disabled-server exclusion in `_check_tool_definitions()`: add a test with a disabled server and assert no HTTP GET issued.
- Static analysis: `uv run ruff check scripts/agent/services/tool_validation.py`, `uv run mypy scripts/agent/services/tool_validation.py`, `uv run bandit scripts/agent/services/tool_validation.py`.

## Completion criteria

- [ ] `_collect_server_tool_names()` skips disabled servers (no HTTP GET issued).
- [ ] Disabled servers do not appear in `server_names` returned from `_check_tool_definitions()`.
- [ ] All existing tests pass without regression.
- [ ] No new lint/type/security errors introduced.

## Out of scope

- Modifying `_check_tool_definitions()`'s strict-mode all-servers-unreachable path (that is covered separately by the existing strict-mode handling).
- Any MCP server business logic unrelated to the startup/discovery path.

## execution_status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260917-070631 | 20260917-070631 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260917-070636 | 20260917-070636 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260917-070640 | 20260917-070640 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-103015_mcpagent01_mcp-server-availability-startup-publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-114735_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-154416
- **Related target files**: scripts/agent/services/tool_validation.py