## Goal

Expose the structured metadata on the HTTP response model (REQ-005) so HTTP and programmatic dispatch return one contract.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- Both fields default so a response built by an early-rejection path (before dispatch) stays valid and reads as `""` and `False`.
- Endpoint tests that assert the exact response body may need the new keys; they are triaged as Fallout (Plan UNK-03).

## Design decisions

- Field names and meaning match `DispatchResult`, so the mapping in `_to_call_tool_response` is one-to-one.

## Alternatives considered

N/A: a single additive pair of fields; no design alternative.

## Implementation
### Target file
`scripts/mcp_servers/models.py`

### Procedure
Add the two fields to `CallToolResponse` with descriptions.

### Method
- Add `execution_mode: str = Field(default="", description=...)` and `side_effect_applied: bool = Field(default=False, description=...)` after `dedup_state` in `CallToolResponse`.
- State in the descriptions that `""` means no dispatcher outcome was attached.

### Details
- `CallToolRequest` is unchanged: the mode never travels in the request body.

### Companion test files
- `tests/mcp_servers/test_models.py`
  - Procedure: Add cases: defaults, round-trip of both fields, and the serialized key set.
  - Validation: `uv run pytest tests/mcp_servers/test_models.py`

## Compatibility considerations

Wire-additive: an older client ignores the new keys; the Agent parser treats them as optional.

## Security considerations

N/A: closed vocabulary and a boolean.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/mcp_servers/test_models.py tests/mcp_servers/test_tool_schema_contract.py`
- `uv run mypy scripts/mcp_servers/models.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- `CallToolResponse` carries both fields with defaults.
- Schema-contract tests pass or are adjusted as Fallout.

## Out of Scope

- Populating the fields (servers and dispatcher documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/mcp_servers/models.py`, `tests/mcp_servers/test_models.py`
