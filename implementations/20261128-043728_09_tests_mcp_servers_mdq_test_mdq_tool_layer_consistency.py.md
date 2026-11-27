## Goal

Add the preview-capability pin for the two MDQ write tools, so the declared capability is asserted
at the same layer that already pins tool-list, dispatch, registry, `is_write`, and `requires_serial`
consistency.

## Scope
**Release unit**: preview path

- One new test in `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`; the existing
  consistency tests (lines 16-41) are unchanged.

## Assumptions

- The capability is read from the producer `TOOL_LIST` declaration, the same source the other pins
  in this file read.
- `scripts/mcp_servers/mdq/mdq_tools.py` declares `none` for all seven mdq entries (lines 76, 110, 146,
  175, 208, 226, 277), so the pin for the two write tools is the only value that changes.

## Design decisions

- The pin belongs in this file rather than in `tests/mcp_servers/mdq/test_mdq_tool_schema.py`,
  because this file is the layer-consistency guard and the schema file pins argument shapes.
- The pin asserts both directions: the two write tools declare `dry_run`, and the remaining mdq
  tools still declare `none`, so a capability added to a read tool would be caught.

## Alternatives considered

- Relying on `tests/mcp_servers/test_tool_schema_contract.py` (line 40), which already asserts the
  field's presence: rejected, presence is not the value, and the no-op contract depends on the
  value matching what the server actually does.

## Implementation
### Target file
`tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`

### Procedure
1. Add `test_write_tools_declare_dry_run_capability` (new): for each `TOOL_LIST` entry whose name is in
   `MDQ_WRITE_TOOLS`, assert `preview_capability == "dry_run"`.
2. Add the complementary assertion that every mdq entry not in `MDQ_WRITE_TOOLS` still declares
   `none`.

### Method

- The test reads `TOOL_LIST` directly, matching the style of `test_write_tools_flagged_is_write`
  (line 36) and `test_serial_tools_flagged_requires_serial` (line 41).

### Details

- Use `MDQ_WRITE_TOOLS` from `shared.tool_constants` as the membership source, so the pin cannot
  drift from the constant the rest of the file already uses.

## Compatibility considerations

- No existing assertion in this file names `preview_capability`, so the new test is additive and no
  expectation is replaced.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- Revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`
- Full sequence per `rules/toolchain.md`.

## Completion criteria

- The capability pin passes for the two write tools and for the read tools (AC-5).

## Out of Scope

- The capability declaration itself: row 1.
- The `dry_run` argument shape: the companion document for row 1.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This row is the test change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Docs row 15 names the dry-run support list |

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
- **Requirement ID**: REQ-003, REQ-007
- **Source issue**: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261127-173835_mdqmcp007_mdq-approval-dry-run.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261128-043728
- **Related target files**: `tests/mcp_servers/mdq/test_mdq_tool_layer_consistency.py`
