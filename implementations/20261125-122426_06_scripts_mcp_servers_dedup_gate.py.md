## Goal

Extend the typed dispatch result with the structured metadata (REQ-005) that replaces output-text inference.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- `DispatchResult` is constructed by keyword everywhere (acquisition branches, the dispatcher, server wrappers), so defaulted trailing fields are compatible.
- The dispatcher normalizes early results with `dataclasses.replace`, so the acquisition code in this module stays untouched.

## Design decisions

- `execution_mode` (new) defaults to the empty string (not set by this module) and `side_effect_applied` (new) to `False`; the dispatcher is the only writer of meaningful values.
- The docstring taxonomy gains idempotency_key_required and the mode vocabulary so the contract is documented where the type lives.

## Alternatives considered

Computing the metadata as read-only properties from `error_type` and `dedup_state` was rejected: a preview has neither, so the mode must be stored.

## Implementation
### Target file
`scripts/mcp_servers/dedup_gate.py`

### Procedure
Add two defaulted fields to `DispatchResult` and extend its docstring.

### Method
- Add `execution_mode: str = ""` and `side_effect_applied: bool = False` after `dedup_state`.
- Extend the `error_type` list in the class docstring with idempotency_key_required (side-effecting call without a key).
- Add a short docstring paragraph defining execution_mode (`preview`, `applied`, no_op) and side_effect_applied.

### Details
- `outcome` property and the overlay cache code are unchanged.

## Compatibility considerations

Additive and defaulted; the frozen dataclass keeps its equality semantics, which now include the two fields.

## Security considerations

N/A: closed vocabulary and a boolean.

## Rollback considerations

N/A: revert the commit; the fields are additive.

## Validation plan

- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py tests/mcp_servers/test_mcp_dispatch_concurrency.py`
- `uv run mypy scripts/mcp_servers/dedup_gate.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- `DispatchResult` exposes both fields with the stated defaults.
- Existing dispatch tests pass.

## Out of Scope

- Setting the fields (dispatcher document).
- Acquisition and lease logic.

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
- **Related target files**: `scripts/mcp_servers/dedup_gate.py`
