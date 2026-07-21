## Goal
Make duplicate tool exclusion findings always produce FATAL status regardless of security profile or strictness in mcp_tool_discovery.py.

## Scope
**In**: 
- Replace conditional severity at line 293-301 in `scripts/agent/services/mcp_tool_discovery.py` with unconditional FATAL for duplicate tool exclusions

**Out**:
- No changes to other findings (drift, etc.) — they still use `_is_fatal_severity()`
- No changes to PRODUCTION mode behavior (was already FATAL)
- No test modifications beyond adding new tests

## Assumptions
1. FATAL findings cause startup abort (confirmed via `pipeline.add_fatal()` at startup.py line 235)
2. The change only affects the duplicate tool detection path, not other duplicate-related logic

## Implementation

### Target file
- `scripts/agent/services/mcp_tool_discovery.py`

### Procedure
1. Locate the duplicate tool detection block around line 293-309
2. Remove the conditional severity based on `_is_fatal_severity()`
3. Set `status = StartupCheckStatus.FATAL` unconditionally for duplicate tool exclusions
4. Run lint/typecheck to confirm no regressions

### Method
Replace the conditional severity check (`self._is_fatal_severity()`) with an unconditional FATAL assignment for duplicate tool exclusions.

### Details

```python
# In scripts/agent/services/mcp_tool_discovery.py, replace lines 293-309:

# Before:
        is_fatal = self._is_fatal_severity()
        findings: list[StartupCheckOutcome] = []
        built: dict[str, RuntimeTool] = {}
        for name, group in by_name.items():
            server_keys = sorted({server_key for server_key, _, _ in group})
            if len(server_keys) > 1:
                status = (
                    StartupCheckStatus.FATAL if is_fatal else StartupCheckStatus.WARNING
                )
                msg = (
                    f"duplicate tool name {name!r} reported by multiple servers: "
                    f"{', '.join(server_keys)} — excluded from registry"
                )
                findings.append(
                    StartupCheckOutcome(source=_SOURCE, status=status, message=msg)
                )
                continue
            server_key, server_url, entry = group[0]
            built[name] = build_runtime_tool(...)

# After:
        findings: list[StartupCheckOutcome] = []
        built: dict[str, RuntimeTool] = {}
        for name, group in by_name.items():
            server_keys = sorted({server_key for server_key, _, _ in group})
            if len(server_keys) > 1:
                # Always fatal — tool is unusable when duplicated across servers
                status = StartupCheckStatus.FATAL
                msg = (
                    f"duplicate tool name {name!r} reported by multiple servers: "
                    f"{', '.join(server_keys)} — excluded from registry"
                )
                findings.append(
                    StartupCheckOutcome(source=_SOURCE, status=status, message=msg)
                )
                continue
            server_key, server_url, entry = group[0]
            built[name] = build_runtime_tool(...)
```

Key points:
- Removed `is_fatal = self._is_fatal_severity()` — no longer needed for this finding type
- `status = StartupCheckStatus.FATAL` is now unconditional for duplicate tool exclusions
- Comment added to explain why this is always FATAL
- Other findings (drift, etc.) still use `_is_fatal_severity()` for their severity determination
- Message format remains unchanged — only severity level changed

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Lint | `ruff check scripts/agent/services/mcp_tool_discovery.py` | 0 errors |
| Type check | `mypy scripts/agent/services/mcp_tool_discovery.py` | no new errors |
| Architecture | `lint-imports` | 0 violations |
| Unit test | `pytest` — mock two MCP servers reporting same tool | FATAL finding in LOCAL mode |
| Unit test | `pytest` — verify other findings still use _is_fatal_severity() | Other findings unchanged |
| Integration test | Manual test run with conflicting MCP servers | Startup fails with clear error |
