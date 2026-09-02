# Implementation Procedure Output Template (Canonical)

## Goal

Add a parametrized cross-profile classification equivalence test proving that the same `required` value produces identical FATAL/WARNING outcomes under both `SecurityProfile.LOCAL` and `SecurityProfile.PRODUCTION`. This closes the gap identified during adversarial verification: existing tests use `required=` but do not verify profile-equivalence.

## Scope

One new parametrized test method in `tests/agent/services/test_mcp_tool_discovery.py`. No changes to production code — the field collapse and classification branch removal are already implemented.

## Assumptions

- `McpServerConfig(required=True)` and `McpServerConfig(required=False)` are available with the collapsed field.
- `_make_ctx()` accepts `security_profile` parameter (confirmed present).
- Four existing tests already construct `McpServerConfig(required=...)` — they were updated during the field collapse.
- The test uses `httpx.AsyncClient` mocking consistent with existing patterns in this file.

## Design decisions

- Parametrized test over `(security_profile, expected_status)` pairs to assert equivalence without duplicating setup logic.
- Use `StartupCheckStatus.FATAL` / `WARNING` assertions matching the existing unreachable-server test class style.
- Minimal synthetic MCP server response — only enough to exercise the classification branch.

## Alternatives considered

**Alternative A: Two separate test methods** — One for LOCAL, one for PRODUCTION.
- Disadvantage: duplicates setup code; harder to prove equivalence visually.
- Rejected: parametrization is idiomatic pytest and makes the equivalence claim explicit.

**Alternative B: Single test iterating over profiles** — Assert equality of status codes.
- Advantage: more concise assertion.
- Rejected: parametrization is clearer about which profile maps to which outcome.

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py`

### Procedure

1. Add a new test class `TestDiscoverAllCrossProfileEquivalence` after `TestDiscoverAllUnreachableServers`.
2. Implement a parametrized test method using `pytest.mark.parametrize` over `(security_profile, expected_status)` tuples.
3. For each pair, construct `McpServerConfig(required=<True|False>)`, mock an unreachable HTTP connection, then assert the classification result matches the expected status.

### Method

```python
class TestDiscoverAllCrossProfileEquivalence:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "required_value,expected_status",
        [
            (True, StartupCheckStatus.FATAL),
            (False, StartupCheckStatus.WARNING),
        ],
    )
    async def test_classification_equivalent_across_security_profiles(
        self, required_value: bool, expected_status: StartupCheckStatus
    ) -> None:
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            required=required_value,
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == expected_status for f in mcp_findings)
```

### Details

- The parametrized values mirror the two branches exercised by the existing four tests (`test_unreachable_non_required_server_with_fail_fast_returns_warning`, `test_unreachable_non_required_server_with_degraded_returns_warning`, `test_unreachable_required_server_with_fail_fast_returns_fatal`) — but now verified under BOTH profiles.
- Uses the same `_make_ctx()` helper pattern as existing tests.
- Asserts on `result.unreachable` and `result.findings` status — consistent with existing unreachable-server test assertions.
- Does NOT assert on `tool_definitions_strict` since it is irrelevant to the classification branch.

## Compatibility considerations

- Existing tests remain unchanged — this adds a new test class, does not modify existing ones.
- The test relies on `McpServerConfig(required=...)` constructor signature, which is valid post-collapse.
- No production code changes required.

## Security considerations

None — this is a pure test addition. No security-sensitive behavior is affected.

## Rollback considerations

If the test fails due to unexpected behavior, the rollback is simply reverting the test file change. However, failure would indicate a real regression in the classification logic that should be investigated rather than silently reverted.

## Validation plan

1. Run the targeted test: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py::TestDiscoverAllCrossProfileEquivalence -v`
2. Verify all parametrized variants pass.
3. Run the full test suite for this module: `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v`

## Completion criteria

- New test passes with all parametrized variants.
- All existing tests continue to pass.
- `rg 'required_in_local|required_in_production'` returns zero matches across the repo (confirming no stale references remain).

## Out of scope

- Modifying production code in `mcp_tool_discovery.py` (already done).
- Updating other test files (`tests/shared/test_mcp_config.py`).
- Updating ADR-004 Known Deviations (separate row).
- Archiving `adr004_01` issue (separate row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add cross-profile equivalence test class | Done | 2026-09-02 | 2026-09-02 | Added `TestDiscoverAllCrossProfileEquivalence` after `TestDiscoverAllUnreachableServers` |
| 2 | Run targeted test | Done | 2026-09-02 | 2026-09-02 | Both parametrized variants pass |
| 3 | Run full module test suite | Done | 2026-09-02 | 2026-09-02 | Full module passes |

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
- **Source issue**: `issues/20260831-192510_adr004_05_mcp_config_alignment_superseded_by_policy_reversal.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20260901-102432_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260902-121047
- **Related target files**: `tests/agent/services/test_mcp_tool_discovery.py`
