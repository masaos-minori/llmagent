## Goal

Replace the pins that assert the current `WRITE_SAFE` tier for the two MDQ write tools with the
tier that maps to `medium`.

## Scope
**Release unit**: tier change and its pins

- `TestMdqSafetyTiers` in `tests/mcp_servers/mdq/test_mdq_routing.py`: the declared-tier assertion
  for `index_paths` and `refresh_index`.

## Assumptions

- Phase 1 pins the current behavior before the declaration changes, so this row is the pin that is
  replaced, not a new assertion added on top of the old one.

## Design decisions

- The pin reads the producer `TOOL_LIST` declaration, which is the single tier source, so the test
  asserts the declaration value rather than a mapping.

## Alternatives considered

- N/A: expectation alignment in one test method.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_routing.py`

### Procedure
1. In `test_mdq_safety_tiers_declared_in_tool_list`, change the expected value for the two write
   tools from `WRITE_SAFE` to `WRITE_DANGEROUS` (lines 96-97).
2. Rename the local set `write_safe` (line 95) to `write_dangerous` so the name matches the tier it
   holds.

### Method

- `test_mdq_write_dangerous_tools` (line 56) asserts membership only and does not name a tier
  value, so it needs no change.

### Details

- The read-tool assertion in the same method (`READ_ONLY` for the remaining mdq tools) is
  unchanged.

## Compatibility considerations

- N/A: no other test asserts the mdq tier value; `tests/agent/test_tool_policy.py` row 11 covers the
  shipped tier-`NONE` set.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_routing.py`

## Completion criteria

- The pin asserts `WRITE_DANGEROUS` for both write tools and the test passes (AC-1, AC-5).

## Out of Scope

- The tier declaration itself: row 1.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs row 14 states the tier |

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
- **Requirement ID**: REQ-001, REQ-007
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_routing.py`
