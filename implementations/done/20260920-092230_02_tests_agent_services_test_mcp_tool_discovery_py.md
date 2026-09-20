## Goal

Update 2 affected tests to expect `FATAL` instead of `WARNING`, and add a `required=False` coverage test case expecting `WARNING`, per REQ-002 and REQ-003.

## Scope

- Update `test_enabled_type_checked_when_present_synthetic` (line ~1176) to expect `FATAL`
- Update `test_malformed_capabilities_produces_warning_not_fatal` (line ~1403) to expect `FATAL`
- Add a new test case verifying `WARNING` status for `required=False` servers

## Assumptions

- Both affected tests use `_server()` which defaults `required=True` (via `McpServerConfig.required = True`)
- A new parametrized variant or separate test function is acceptable for `required=False` coverage rather than modifying all existing tests
- The 2 unrelated `TestDiscoverAllCrossProfileEquivalence` failures remain out of scope

## Design decisions

- Change only the specific assertions that fail due to the FATAL escalation; do not modify other assertions in the same test functions
- For `required=False` coverage, add a new test function rather than parametrizing existing ones — minimal scope expansion

## Alternatives considered

- Adding a `required=False` parameter to `_server()` in all existing tests — rejected as unnecessary scope expansion; only one new test case needs `required=False` coverage

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

#### Phase 1: Update `test_enabled_type_checked_when_present_synthetic`

Change the assertion on line 1176:

**Before:**
```python
assert enabled_findings[0].status == StartupCheckStatus.WARNING
```

**After:**
```python
assert enabled_findings[0].status == StartupCheckStatus.FATAL
```

#### Phase 2: Update `test_malformed_capabilities_produces_warning_not_fatal`

Change the assertion on line 1403:

**Before:**
```python
assert capability_findings[0].status == StartupCheckStatus.WARNING
```

**After:**
```python
assert capability_findings[0].status == StartupCheckStatus.FATAL
```

Note: The test name `test_malformed_capabilities_produces_warning_not_fatal` becomes misleading after this change. Consider renaming it to reflect the actual behavior (e.g., `test_malformed_capabilities_produces_fatal_for_required_server`). However, renaming is optional — the assertion fix is the primary requirement. If renaming, also update the test name in the assertion message check on line 1404.

#### Phase 3: Add `required=False` coverage test

Add a new test function after `test_malformed_capabilities_produces_warning_not_fatal`:

```python
@pytest.mark.asyncio
async def test_malformed_capabilities_produces_warning_for_non_required_server() -> None:
    """Verify WARNING (not FATAL) when server has required=False."""
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "bad_tool",
                        "description": "malformed capabilities",
                        "inputSchema": {"type": "object", "properties": {}},
                        "capabilities": "filesystem.read",
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": [],
                    }
                ],
            },
        )
    )
    # Override required=False via the server config
    ctx = _make_ctx({"fs": _server(required=False)}, http)

    result = await McpToolDiscoveryService(ctx).discover_all()

    assert result.registry.all_tools() == []
    capability_findings = [f for f in result.findings if "capabilities" in f.message]
    assert len(capability_findings) == 1
    assert capability_findings[0].status == StartupCheckStatus.WARNING
    assert "bad_tool" in capability_findings[0].message
```

However, `_server()` does NOT accept a `required` parameter currently. Two options:

**Option A**: Extend `_server()` to accept an optional `required` parameter:

In the `_server()` helper (around line 67-76):

**Before:**
```python
def _server(
    url: str = "http://127.0.0.1:9000",
    startup_mode: StartupMode = StartupMode.PERSISTENT,
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        startup_mode=startup_mode,
        auth_token="test-token",
    )
```

**After:**
```python
def _server(
    url: str = "http://127.0.0.1:9000",
    startup_mode: StartupMode = StartupMode.PERSISTENT,
    required: bool = True,
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        startup_mode=startup_mode,
        auth_token="test-token",
        required=required,
    )
```

Then use `_server(required=False)` in the new test. This approach reuses the existing helper pattern and keeps the test readable.

### Details

1. **Phase 1**: Edit line 1176 — change `WARNING` to `FATAL`
2. **Phase 2**: Edit line 1403 — change `WARNING` to `FATAL`; optionally rename the test function
3. **Phase 3a**: Extend `_server()` helper at line 67-76 to accept `required` parameter
4. **Phase 3b**: Add the new test function after line 1405

## Compatibility considerations

- Test behavior changes: two existing tests will now pass where they previously failed (due to the FATAL escalation being intentional)
- No backward compatibility impact — these are internal tests, not public API consumers
- The renamed test (if chosen) would break CI references to the old test name

## Security considerations

No security impact. These are test updates reflecting existing runtime behavior.

## Rollback considerations

Revert all three phases if the Plan's assumption about REQ-008 being intentional proves incorrect. Each phase can be rolled back independently.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_enabled_type_checked_when_present_synthetic` | Unit — verify test expects FATAL | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py::test_enabled_type_checked_when_present_synthetic -q` | Pass (assertion updated to FATAL) |
| `test_malformed_capabilities_produces_warning_not_fatal` | Unit — verify test expects FATAL | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py::test_malformed_capabilities_produces_warning_not_fatal -q` | Pass (assertion updated to FATAL) |
| New `required=False` test | Unit — verify test passes with WARNING | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -k "non_required" -q` | Pass (asserts WARNING) |
| Full test suite | Integration — verify no regressions | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -q` | 0 new failures; 2 pre-existing `TestDiscoverAllCrossProfileEquivalence` failures remain |

## Completion criteria

- `test_enabled_type_checked_when_present_synthetic` asserts `.status == StartupCheckStatus.FATAL`
- `test_malformed_capabilities_produces_warning_not_fatal` asserts `.status == StartupCheckStatus.FATAL`
- New `required=False` test exists and asserts `.status == StartupCheckStatus.WARNING`
- All three tests pass individually and as a group

## Out of scope

- Modifying `_fetch_server_tools()`'s escalation logic
- Updating `_validate_and_normalize_entry()`'s docstring (covered by separate implementation procedure)
- Fixing unrelated `TestDiscoverAllCrossProfileEquivalence` failures
- Renaming the test `test_malformed_capabilities_produces_warning_not_fatal` (optional, not required)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260919-164314_mcpdisc01_mcp_tool_discovery-escalates-per-entry-warning-findings-to-fatal-for-required-servers,-contradicting-docstring-and-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260920-090540_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260920-092230
- **Related target files**: tests/agent/services/test_mcp_tool_discovery.py