## Goal

Remove the `build_discovery_map` import, delete its sole consuming test method `test_duplicate_live_ownership_detected`, and correct the stale class docstring in `tests/shared/test_tool_registry.py`.

## Scope

- Remove `build_discovery_map` from the import statement on line 14 (`from shared.route_resolver import build_discovery_map`)
- Delete `test_duplicate_live_ownership_detected` method (lines 243-265) from `TestStartupValidationStrictMode`
- Correct the stale class docstring (lines 162-167) which cites both `build_discovery_map()` and a non-existent `check_routing_drift_vs_live()` function
- No other files are modified in this row

## Assumptions

- `TestDuplicateOwnershipRejection` (lines 71-79, tests `ToolRegistry.register()`) is unrelated and stays untouched.
- The remaining methods in `TestStartupValidationStrictMode` (testing `validate_routing_against_live()`) do not depend on `build_discovery_map`.

## Design decisions

- Complete removal of the import and test method rather than partial cleanup: the entire method tests only `build_discovery_map()`, which is removed by REQ-001.
- Correction of the stale class docstring as part of this change: the docstring references both `build_discovery_map()` (removed) and `check_routing_drift_vs_live()` (never existed), making it doubly stale.

## Alternatives considered

- Keeping the method but modifying it to test the canonical exclude-and-FATAL policy — rejected: that would require adding new production code dependencies and is covered by the existing suite in `tests/agent/services/test_mcp_tool_discovery.py`.

## Implementation

### Target file

`tests/shared/test_tool_registry.py`

### Procedure

Remove the `build_discovery_map` import, delete its sole consuming test method, and correct the stale class docstring in `test_tool_registry.py`.

### Method

1. Remove `build_discovery_map` from the import statement on line 14:
   - Change: `from shared.route_resolver import build_discovery_map`
   - To: remove the entire import line (if no other imports from `route_resolver` remain in the file) or keep only needed imports.
2. Delete `test_duplicate_live_ownership_detected` method (lines 243-265) from `TestStartupValidationStrictMode`.
3. Correct the class docstring (lines 162-167) to remove references to both `build_discovery_map()` and `check_routing_drift_vs_live()`.

### Details

```python
# Line 14: check if there are other imports from route_resolver in this file:
# If only build_discovery_map was imported:
# Before:
from shared.route_resolver import build_discovery_map

# After:
# (remove the entire import line)

# Lines 162-167: correct the stale class docstring:
# Before:
class TestStartupValidationStrictMode:
    """Tests for the four strict-mode drift conditions checked at startup.

    These tests verify the behavior of validate_routing_against_live() and
    build_discovery_map() for each condition that check_routing_drift_vs_live()
    must detect.
    """

# After:
class TestStartupValidationStrictMode:
    """Tests for the four strict-mode drift conditions checked at startup.

    These tests verify the behavior of validate_routing_against_live() for each
    condition that must be detected.
    """

# Lines 243-265: delete entirely:
def test_duplicate_live_ownership_detected(
    self, caplog: pytest.LogCaptureFixture
) -> None:
    """Condition 4: same tool returned by two different servers.

    build_discovery_map() must log a WARNING about the duplicate.
    """
    with caplog.at_level(logging.WARNING):
        route_map, duplicates = build_discovery_map(
            {
                "server_a": [{"name": "shared_tool", "server_key": "server_a"}],
                "server_b": [{"name": "shared_tool", "server_key": "server_b"}],
            }
        )
    # First occurrence wins
    assert route_map == {"shared_tool": "server_a"}
    assert duplicates == {"shared_tool": ["server_a", "server_b"]}
    # Warning must have been logged
    assert any(
        "shared_tool" in r.message
        for r in caplog.records
        if r.levelno >= logging.WARNING
    )
```

## Compatibility considerations

- Remaining tests in this file (`TestDuplicateOwnershipRejection`, `TestAllToolConstantsFrozensetsRegistered`) are unaffected.
- Remaining methods in `TestStartupValidationStrictMode` (testing `validate_routing_against_live()`) are unaffected — they do not depend on `build_discovery_map`.
- `pytest --collect-only tests/shared/test_tool_registry.py` will collect fewer tests after this change.

## Security considerations

- No security impact. This is a test file modification.

## Rollback considerations

- Reverting this change restores the deleted test method and import. If needed later, the test should be rewritten to cover the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/shared/test_tool_registry.py -v` to confirm no import error for removed symbols and that remaining `TestStartupValidationStrictMode`/`TestDuplicateOwnershipRejection`/`TestAllToolConstantsFrozensetsRegistered` tests pass unchanged.
- Collection check: `uv run pytest --collect-only tests/shared/test_tool_registry.py` — confirm no tests collected from `test_duplicate_live_ownership_detected`.
- Static analysis: `uv run ruff check tests/shared/test_tool_registry.py`, `uv run mypy tests/shared/test_tool_registry.py`.

## Completion criteria

- `build_discovery_map` removed from the import statement on line 14.
- `test_duplicate_live_ownership_detected` method deleted from `TestStartupValidationStrictMode`.
- Class docstring corrected to remove references to both `build_discovery_map()` and `check_routing_drift_vs_live()`.
- All remaining tests in the file continue to pass without referencing removed symbols.
- No new lint/type errors introduced.

## Out of scope

- Modifying `TestDuplicateOwnershipRejection` — unrelated class testing `ToolRegistry.register()`.
- Changes to `docs/*.md` — deferred to REQ-001's Documentation Impact item.
- Adding new tests — this row is purely subtractive.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove build_discovery_map import, delete test_duplicate_live_ownership_detected, correct docstring | Completed | 20260917-213331 | 20260917-213331 |  |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-213331 | 20260917-213331 |  |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-103315_mcpagent08_duplicate-tool-ownership-routing-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-130526_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-230424
- **Related target files**: tests/shared/test_tool_registry.py