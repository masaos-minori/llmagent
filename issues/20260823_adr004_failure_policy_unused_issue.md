# Known Issue: ADR-004 Decision #8 — `failure_policy` defined but never enforced

## Metadata

- **ID**: ADR-004-D8-failure-policy-unused
- **Status**: Open
- **Severity**: Medium
- **Area**: Startup validation / MCP server configuration
- **Related ADR**: ADR-004 (Environment Profile別障害方針 — Fail-Fast/Fail-Open)
- **Created**: 2026-08-23

## Conflicting Source

- **ADR text**: Decision #8 defines three failure policies per MCP server: `fail-fast`, `disable-tool`, `degraded`
- **Expected design**: Each MCP server can specify its own failure policy, allowing different handling strategies (immediate abort vs. tool disable vs. degraded operation)
- **Observed implementation**: Only `required_in_production` / `required_in_local` flags are used (binary FATAL/WARNING). The `failure_policy` field is defined in config but never consulted anywhere in the codebase.

## Expected Design

ADR-004 Decision #8 specifies:

```text
required_in_production = true | false
required_in_local = true | false
failure_policy = fail-fast | disable-tool | degraded
```

The intent is that when an MCP server becomes unreachable:
- `fail-fast`: Abort startup immediately (equivalent to current FATAL behavior)
- `disable-tool`: Continue startup but mark tools from this server as unavailable
- `degraded`: Continue startup with reduced capability, log warning

## Observed Implementation

Current implementation in `scripts/agent/services/mcp_tool_discovery.py:131-134`:

```python
is_prod = self._ctx.cfg.mcp.security_profile == SecurityProfile.PRODUCTION
is_required = cfg.required_in_production if is_prod else cfg.required_in_local
new_status = StartupCheckStatus.FATAL if is_required else StartupCheckStatus.WARNING
```

Only two outcomes exist:
1. Server is required → FATAL (abort)
2. Server is not required → WARNING (continue)

There is no third outcome (`disable-tool`) or fourth outcome (`degraded`). The `failure_policy` field exists in `McpServerConfig` but is never read.

## Impact

- MCP servers cannot express nuanced failure tolerance beyond binary required/not-required
- Production deployments lose flexibility: some non-critical servers could be disabled without aborting instead of requiring full abort
- Local development loses flexibility: some non-critical servers could be marked as degraded rather than just warning

## Recommended Action

1. Implement `failure_policy` enforcement in `McpToolDiscoveryService._fetch_server_tools()`
2. For `disable-tool`: add server to unavailable list but don't set FATAL finding
3. For `degraded`: add WARNING finding but allow startup to continue even if server is required
4. Update `startup.py` pipeline to respect these different severity levels
5. Add integration test verifying each policy produces correct startup behavior

## Owner

Agent team

## Resolution Target

Before ADR-004 moves from Proposed to Accepted status
