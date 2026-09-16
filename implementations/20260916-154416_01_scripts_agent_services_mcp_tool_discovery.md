## Goal

Add `cfg.startup_mode != StartupMode.NONE` to `McpToolDiscoveryService.discover_all()`'s per-server skip condition, so that a disabled (`StartupMode.NONE`) server is never probed during discovery. (REQ-001; "No network request is sent to a disabled server during discovery")

## Scope

- Modify `discover_all()`'s per-server loop to also check `cfg.startup_mode != StartupMode.NONE` alongside the existing `cfg.transport != TransportType.HTTP or not cfg.url` condition.
- Add a post-discovery required-tool-presence check: for every required server's configured `tool_names`, confirm each name was actually discovered (present in the built registry); missing means FATAL. (REQ-009)
- Extend `_validate_and_normalize_entry()`'s caller to escalate malformed entries belonging to a `required=True` server to FATAL instead of WARNING. (REQ-008)

## Assumptions

- `StartupMode.NONE` is defined in `scripts/shared/mcp_config.py` and has an `is_disabled` property on `McpServerConfig` that returns `True` when `startup_mode == StartupMode.NONE`.
- The `_REQUIRED_SCHEMA_V2_FIELDS` constant and `validate_tool_schema_v2()` function remain unchanged; REQ-008 only changes the severity level of findings, not the validation logic itself.
- A required server's `tool_names` list is populated via config (`McpServerConfig.tool_names`), and a missing tool means the server is misconfigured rather than transiently unavailable.

## Design decisions

- Use `cfg.is_disabled` (the existing property on `McpServerConfig`) as the single predicate for disabling a server, consistent with how other parts of the codebase derive "disabled" status. This avoids four independent re-derivations of "is this server disabled" drifting apart over time.
- For REQ-008, add the `required` flag check at the call site of `_validate_and_normalize_entry()` (inside `_fetch_server_tools()`) rather than inside `_validate_and_normalize_entry()` itself, because the method currently has no access to `McpServerConfig` and changing its signature would ripple across callers.
- For REQ-009, implement the required-tool-presence check after `_dedupe_and_build()` returns but before returning the `DiscoveryResult`, using the same `findings` list that carries other FATAL/WARNING outcomes.

## Alternatives considered

- Adding a new `is_none_mode` property on `StartupMode` — unnecessary since `is_disabled` already covers this.
- Checking `cfg.startup_mode` directly instead of `cfg.is_disabled` — equivalent but less semantic; `is_disabled` is the established convention.
- Moving the `required` check into `_validate_and_normalize_entry()` — would require threading `McpServerConfig` through the method signature, which is a broader change scope than needed here.

## Compatibility considerations

- Existing non-disabled servers are unaffected; the added `cfg.is_disabled` check only short-circuits the loop earlier for disabled servers.
- The FATAL escalation for required-server malformed entries (REQ-008) may turn previously-WARNING-only production deployments into one that fails to start, if a currently-deployed required server has a malformed or missing tool today. This is the Issue's explicit intent.
- The required-tool-presence check (REQ-009) similarly may fail startup for a required server whose `tool_names` includes tools that were removed from the server's `/v1/tools` response.

## Security considerations

- Blocking network requests to disabled servers prevents potential lateral movement via a disabled-but-resolvable MCP endpoint.
- Escalating malformed entries on required servers to FATAL ensures that a compromised or misconfigured server cannot silently degrade security posture.

## Rollback considerations

- Reverting the `is_disabled` check in `discover_all()` restores the pre-fix behavior where disabled servers could be probed.
- Removing the FATAL escalation for required-server malformed entries restores the pre-fix WARNING-only behavior.
- Removing the required-tool-presence check restores the pre-fix silent-miss behavior.

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py`

### Procedure

1. **Phase 1: Discovery-layer exclusion**
   - In `discover_all()`'s per-server loop, add `or cfg.is_disabled` to the existing skip condition on line 127.
   - Current code: `if cfg.transport != TransportType.HTTP or not cfg.url:`
   - New code: `if cfg.transport != TransportType.HTTP or not cfg.url or cfg.is_disabled:`

2. **Phase 3a: Required-tool FATAL escalation**
   - Inside `_fetch_server_tools()`, after calling `_validate_and_normalize_entry()`, check if the entry is malformed (finding is not None) AND the owning server's `cfg.required` is True.
   - If both conditions hold, replace the finding's status from `WARNING` to `FATAL`.
   - Current pattern: `return _warning_entry(...)` always produces WARNING.
   - New pattern: after `_validate_and_normalize_entry()` returns `(normalized, finding)`, if `finding is not None` and `cfg.required`, set `finding.status = StartupCheckStatus.FATAL` before appending to `entry_findings`.

3. **Phase 3b: Required-tool-presence check**
   - After `_dedupe_and_build(entries)` returns in `discover_all()`, iterate over all servers where `cfg.required` is True and `cfg.tool_names` is non-empty.
   - For each required server, check that every name in `cfg.tool_names` exists as a key in the returned registry's `_tools` dict.
   - For each missing tool name, append a FATAL finding to `findings`.

### Method

- **Step 1**: Edit `discover_all()` at line 127 — add `or cfg.is_disabled` to the skip condition.
- **Step 2**: Edit `_fetch_server_tools()` after the `_validate_and_normalize_entry()` call — add conditional FATAL escalation based on `cfg.required`.
- **Step 3**: Edit `discover_all()` after the `_dedupe_and_build()` call — add the required-tool-presence check loop.

### Details

**Step 1 — `discover_all()` skip condition:**

```python
# Before (line 127):
if cfg.transport != TransportType.HTTP or not cfg.url:
    continue

# After:
if cfg.transport != TransportType.HTTP or not cfg.url or cfg.is_disabled:
    continue
```

**Step 2 — Required-tool FATAL escalation in `_fetch_server_tools()`:**

After the `_validate_and_normalize_entry()` call (around line 248-254):

```python
for raw_entry in tools:
    normalized, finding = self._validate_and_normalize_entry(
        key, cfg.url, raw_entry
    )
    # REQ-008: escalate malformed entries to FATAL for required servers
    if finding is not None and cfg.required:
        finding = StartupCheckOutcome(
            source=finding.source,
            status=StartupCheckStatus.FATAL,
            message=finding.message,
            remediation=finding.remediation,
        )
    if finding is not None:
        entry_findings.append(finding)
    if normalized is not None:
        entries.append((key, cfg.url, normalized))
```

**Step 3 — Required-tool-presence check in `discover_all()`:**

After `_dedupe_and_build(entries)` returns (around line 155):

```python
registry, dedup_findings = self._dedupe_and_build(entries)
findings.extend(dedup_findings)

# REQ-009: verify every required server's declared tool_names are present
for srv_key, srv_cfg in self._ctx.cfg.mcp.mcp_servers.items():
    if srv_cfg.required and srv_cfg.tool_names:
        for tool_name in srv_cfg.tool_names:
            if tool_name not in registry._tools:
                findings.append(
                    StartupCheckOutcome(
                        source=_SOURCE,
                        status=StartupCheckStatus.FATAL,
                        message=(
                            f"{srv_key}: required tool {tool_name!r} not found in discovery results"
                        ),
                        remediation="Verify the server's /v1/tools response includes this tool.",
                    )
                )
```

## Validation plan

- Run unit tests: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`
- Verify disabled-server exclusion: add a test case with `startup_mode=NONE` and assert `http.get.assert_not_called()`.
- Verify required-tool FATAL escalation: add a test with a required server having a malformed tool entry, assert `StartupCheckStatus.FATAL`.
- Verify required-tool-presence: add a test with a required server declaring a tool name not in the discovery result, assert FATAL outcome.
- Static analysis: `uv run ruff check scripts/agent/services/mcp_tool_discovery.py`, `uv run mypy scripts/agent/services/mcp_tool_discovery.py`, `uv run bandit scripts/agent/services/mcp_tool_discovery.py`.

## Completion criteria

- [ ] `discover_all()` skips disabled servers (no HTTP GET issued).
- [ ] Malformed entries on required servers produce FATAL findings.
- [ ] Missing required-tool names produce FATAL findings.
- [ ] All existing tests pass without regression.
- [ ] No new lint/type/security errors introduced.

## Out of scope

- Modifying `_validate_and_normalize_entry()`'s internal validation logic (only the severity escalation is in scope).
- Handling optional-server degraded states beyond what already exists (optional-server unreachable remains WARNING).
- Any MCP server business logic unrelated to the startup/discovery path.

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
- **Requirement ID**: REQ-001, REQ-008, REQ-009
- **Source issue**: issues/20260914-103015_mcpagent01_mcp-server-availability-startup-publication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-114735_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-154416
- **Related target files**: scripts/agent/services/mcp_tool_discovery.py
