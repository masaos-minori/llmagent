## Goal

Delete `tests/shared/test_routing_duplicate_ownership.py` in full — every test in this file exercises only the removed `build_discovery_map()` function.

## Scope

- Delete the entire file `tests/shared/test_routing_duplicate_ownership.py` (59 lines)
- No other files are modified in this row

## Assumptions

- Every test function in this file imports and calls only `build_discovery_map`, which is removed by REQ-001
- No production code depends on this test file being present

## Design decisions

- Complete deletion rather than partial cleanup: the file exists solely to test `build_discovery_map()`, which is removed in the same change.

## Alternatives considered

- Moving the file to a deprecated directory — rejected: unnecessary; the tests exercise dead code that no longer exists.
- Keeping the file as historical reference — rejected: it asserts incorrect policy (first-wins routing) as correct, which would mislead future readers.

## Implementation

### Target file

`tests/shared/test_routing_duplicate_ownership.py`

### Procedure

Delete the entire file `tests/shared/test_routing_duplicate_ownership.py`.

### Method

1. Remove the file using `git rm tests/shared/test_routing_duplicate_ownership.py`.
2. Verify the file is absent from the filesystem after the change.

### Details

```bash
# Delete the file:
git rm tests/shared/test_routing_duplicate_ownership.py

# Verify deletion:
test -f tests/shared/test_routing_duplicate_ownership.py && echo EXISTS || echo REMOVED
```

## Compatibility considerations

- No production code depends on this test file existing.
- `pytest --collect-only tests/shared/` will no longer collect any tests from this file.

## Security considerations

- No security impact. This is a test file deletion.

## Rollback considerations

- Reverting this change restores the test file. If needed later, the tests should be rewritten to cover the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Deletion check: `test -f tests/shared/test_routing_duplicate_ownership.py && echo EXISTS || echo REMOVED` — expect REMOVED.
- Collection check: `uv run pytest --collect-only tests/shared/` — confirm no tests collected from this file.
- Regression: run `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v -k duplicate` to reconfirm the canonical duplicate-ownership suite still passes unmodified.

## Completion criteria

- File `tests/shared/test_routing_duplicate_ownership.py` no longer exists on disk.
- `pytest --collect-only tests/shared/` does not list any tests from this file.
- No remaining references to deleted symbols (`build_discovery_map`, `ToolDescriptor`) in any other test file.

## Out of scope

- Modifying any other test file — covered by separate rows (REQ-003, REQ-004).
- Adding new tests — this row is purely subtractive.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete tests/shared/test_routing_duplicate_ownership.py | Completed | 20260917-213211 | 20260917-213211 |  |
| 2 | Run the validation sequence (rules/toolchain.md) | Completed | 20260917-213211 | 20260917-213211 |  |

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
- **Source issue**: issues/20260914-103315_mcpagent08_duplicate-tool-ownership-routing-policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-130526_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-230424
- **Related target files**: tests/shared/test_routing_duplicate_ownership.py