## Goal

Add `cfg.startup_mode != StartupMode.NONE` to `McpToolDiscoveryService._fetch_server_tools()`'s per-server skip condition, so that a disabled (`StartupMode.NONE`) server is never probed during the static-vs-live tool-definition drift check. (REQ-001; "No network request is sent to a disabled server during discovery")

## Scope

- Modify `_fetch_server_tools()`'s per-server loop to also check `cfg.startup_mode != StartupMode.NONE` alongside the existing `cfg.transport != TransportType.HTTP or not cfg.url` condition.

## Assumptions

- `StartupMode.NONE` is defined in `scripts/shared/mcp_config.py` and `McpServerConfig.is_disabled` returns `True` when `startup_mode == StartupMode.NONE`.
- The `McpToolDiscoveryService` constructor accepts `server_configs: dict[str, McpServerConfig]` as its first argument (after `ctx`), consistent with how `ToolTransportInvoker.__init__` receives configs.

## Design decisions

- Use `cfg.is_disabled` as the single predicate, consistent with how other parts of the codebase derive "disabled" status. This avoids four independent re-derivations of "is this server disabled" drifting apart over time.
- Skip probing entirely rather than probing a "null entry" — simpler and more efficient.

## Alternatives considered

- Adding a new `is_none_mode` property on `StartupMode` — unnecessary since `is_disabled` already covers this.
- Probing a null/no-op entry for disabled servers — adds unnecessary complexity; skipping probing is cleaner.
- Checking `cfg.startup_mode` directly instead of `cfg.is_disabled` — equivalent but less semantic; `is_disabled` is the established convention.

## Compatibility considerations

- Existing non-disabled servers are unaffected; the added `is_disabled` check only prevents registry publication for disabled servers.
- A disabled server excluded by this change will not appear in the registry's `_tools` dict, which is consistent with treating it as "not configured."

## Security considerations

- Preventing registry publication for disabled servers eliminates the possibility of a disabled server's tools being available for execution even if other gates are bypassed.

## Rollback considerations

- Reverting the `is_disabled` check in `_fetch_server_tools()` restores the pre-fix behavior where disabled servers get their tools published to the registry.

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

1. **Phase 1: Discovery-layer exclusion**
   - In `_fetch_server_tools()`'s per-server loop, add `or cfg.is_disabled` to the existing skip condition on line 158.
   - Current code: `if cfg.transport != TransportType.HTTP or not cfg.url:`
   - New code: `if cfg.transport != TransportType.HTTP or not cfg.url or cfg.is_disabled:`

### Method

- Edit `_fetch_server_tools()` at line 158 — add `or cfg.is_disabled` to the skip condition.

### Details

**Step 1 — `_fetch_server_tools()` skip condition:**

```python
# Before (line 158):
if cfg.transport != TransportType.HTTP or not cfg.url:
    continue

# After:
if cfg.transport != TransportType.HTTP or not cfg.url or cfg.is_disabled:
    continue
```

## Validation plan

- Run unit tests: `uv run pytest tests/agent/test_startup*.py -v`
- Verify disabled-server not included: add a test with `startup_mode=NONE` and assert the server was not added to the built `McpConfig`.
- Static analysis: `uv run ruff check scripts/agent/startup_validation.py`, `uv run mypy scripts/agent/startup_validation.py`, `uv run bandit scripts/agent/startup_validation.py`.

## Completion criteria

- [ ] `_fetch_server_tools()` skips disabled servers (no registry publication).
- [ ] Disabled servers do not appear in the registry's `_tools` dict.
- [ ] All existing tests pass without regression.
- [ ] No new lint/type/security errors introduced.

## Out of scope

- Modifying `_fetch_server_tools()`'s strict-mode all-servers-unreachable path (that is covered separately by the existing strict-mode handling).
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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260914-103015_mcpagent01_mcp-server-availability-startup-publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-114735_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-154416
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py
