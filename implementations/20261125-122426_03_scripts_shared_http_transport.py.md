## Goal

Send the execution mode as `X-Execution-Mode` and read the result metadata back (REQ-007), so the Agent's approval preview (REQ-008) travels with its own mode.

## Scope
**Release unit**: R1-mode-contract

## Assumptions

- The call is already refused without a logical call id (wire gate); the new header is added next to `X-Idempotency-Key` and does not change that gate.
- Both response fields are optional on the wire so an older server keeps working; the Agent then reads `""` and `False`.

## Design decisions

- The header is a cross-check, not an authority: the server resolves the mode from the arguments itself and rejects a disagreement (server procedure).
- A response `execution_mode` outside the closed vocabulary is a protocol error and takes the existing `ValueError` path, so a bad value never silently becomes metadata.

## Alternatives considered

Putting the mode in the JSON body was rejected: `CallToolRequest` is a pinned public schema and a header is how the key already travels.

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
Add the header at the single header-building site and extend `_parse_http_response`.

### Method
- In `HttpTransport.call`, after `headers["X-Idempotency-Key"] = context.call_id`, set `headers["X-Execution-Mode"] = context.execution_mode`.
- In `_parse_http_response`, read optional `execution_mode` (must be `str` in `EXECUTION_MODES` or empty) and optional `side_effect_applied` (must be `bool`); raise `ValueError` for a wrong type or an unknown mode.
- Pass both to `ToolCallResult.from_transport`.

### Details
- `_tool_error_result` (tool-level statuses) is unchanged: an error body carries no metadata and the result keeps the defaults.
- Do not log header values beyond what the existing code logs.

### Companion test files
- `tests/shared/test_http_transport.py`
  - Procedure: Add cases: the header equals the context mode for applied and preview; the parsed result carries the metadata; absent fields default; a wrong type and an unknown mode raise through the transport error path.
  - Validation: `uv run pytest tests/shared/test_http_transport.py`

## Compatibility considerations

Wire-additive in both directions; an old server ignores the header and omits the fields.

## Security considerations

The header carries a closed vocabulary value only.

## Rollback considerations

N/A: revert the commit; both sides tolerate the absence of the header and the fields.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py`
- `uv run mypy scripts/shared/http_transport.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Every `call_tool` request carries `X-Execution-Mode`.
- Parsed results carry `execution_mode` and `side_effect_applied`, defaulting when absent.

## Out of Scope

- The server-side cross-check.
- Retry policy and the write-tool retry suppression.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — |  |
| 2 | Add the companion test per Validation plan | Pending | — | — |  |
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
- **Requirement ID**: REQ-007, REQ-008
- **Source issue**: issues/20261119-140512_mcpai005_structured-execution-context.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-121807_mcpai005_structured-execution-context.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-122426
- **Related target files**: `scripts/shared/http_transport.py`, `tests/shared/test_http_transport.py`
