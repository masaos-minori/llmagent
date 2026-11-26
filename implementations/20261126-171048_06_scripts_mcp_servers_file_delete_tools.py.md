## Goal
- Generate the delete tool schemas from the strict models with the shared generator (REQ-001, shared schema source).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the two hand-maintained `inputSchema` dicts at lines 20, 51.
- Out of scope: the model base swap (seq 05).

## Assumptions
- Verified in Step 3a: hand-maintained dicts confirmed at the cited lines.

## Design decisions
- Use `build_input_schema()` from `scripts/mcp_servers/request_contract.py` as the single schema source for both delete tools.

## Alternatives considered
- N/A: single-source change with no contract decision of its own.

## Implementation
### Target file
`scripts/mcp_servers/file/delete_tools.py`

### Procedure
1. Import `build_input_schema` from `scripts/mcp_servers/request_contract.py`.
2. Replace each hand-maintained `inputSchema` dict with `build_input_schema(model)` for the corresponding request model.

### Method
- N/A: mechanical replacement.

### Details
- The consistency tests in seq 20 pin runtime and discovery schema equality after the switch.

## Compatibility considerations
- N/A: the generated schema matches the hand-written contract for valid requests; extra fields were already forbidden.

## Security considerations
- N/A: no secrets.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/mcp_servers/file/test_file_schema_consistency.py -v` (seq 20); full `rules/toolchain.md` sequence.

## Completion criteria
- No hand-maintained `inputSchema` dict remains; both delete tool schemas are generated from the strict models; tests pass (AC-1).

## Out of Scope
- Model inheritance (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (shared strict base and shared schema generator)
- **Source issue**: issues/20261119-140516_mcpai009_file-mcp-hardening.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-065258_mcpai009_file-mcp-hardening.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-171048
- **Related target files**: `scripts/mcp_servers/file/delete_tools.py`
