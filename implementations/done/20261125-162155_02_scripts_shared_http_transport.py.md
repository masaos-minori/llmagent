## Goal

Parse `dedup_state` from MCP responses in both result builders of `HttpTransport` (REQ-002, the transport currently drops the field).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Sequencing: execute after the pending mcpai005 procedure `implementations/20261125-122426_03_scripts_shared_http_transport.py.md` if it edits this file; re-read the file before editing.
- `ToolCallResult.dedup_state` exists by then (row 1 procedure); this document does not add the field itself.
- Dedup refusals arrive as HTTP 200 with `is_error: true` (Plan Assumptions); the tolerant 4xx parse is defensive.

## Design decisions

- Tolerant extraction only: a missing or non-string `dedup_state` yields `""` and must not raise or change error classification (REQ-002).
- No vocabulary validation in the transport (REQ-002); the value is stored as reported.

## Alternatives considered

Validating the value against the server state set was rejected: `shared` cannot import `mcp_servers` and the state set may change server-side.

## Implementation
### Target file
`scripts/shared/http_transport.py`
### Procedure
Pass the parsed `dedup_state` into `ToolCallResult.from_transport` in both builders.

### Method
- In `_parse_http_response` (line 100), read `data.get("dedup_state")`; pass it to `from_transport` when it is a `str`, otherwise `""`.
- In `_tool_error_result` (line 146; 124 at generation, drifted), read `dedup_state` from the parsed body inside the existing try block; a parse failure or non-string value keeps the current fallback behavior and yields `""`.

### Details
- The existing `detail`/`result` fallback for malformed tool-level bodies is unchanged; only an additional optional key is read.
- The transport-failure path (`_transport_error`, line 166; 148 at generation, drifted) builds results without a body, so it keeps `""`; no change there.

### Companion test files
- `tests/shared/test_http_transport.py`
  - Procedure: add parser tests for each dedup state on success and on 200-with-`is_error`, for a missing field, for a non-string value, and for tool-level-status bodies with and without `dedup_state` (REQ-002, AC-1, AC-2).
  - Validation: `uv run pytest tests/shared/test_http_transport.py`

## Compatibility considerations

Responses without the field keep the current result shape with `""` (REQ-006); error classification is unchanged (AC-2).

## Security considerations

N/A: no new parsing of credentials or user content; the value is an opaque server-reported string.

## Rollback considerations

N/A: revert the commit; the parse is additive.

## Validation plan

- `uv run pytest tests/shared/test_http_transport.py`
- `uv run mypy scripts/shared/http_transport.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- Every response shape named in REQ-002 yields the reported `dedup_state` or `""`.
- Existing transport tests pass unchanged.

## Out of Scope

- Defining the DTO field (row 1 procedure).
- Passing the value to the audit log (row 5/6 procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125 | Step 3a verified: builders at 100/146; line drift noted |
| 2 | Add the companion test per Validation plan | Completed | — | 20261125 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261125 | 56 passed; mypy/ruff clean |

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
- **Requirement ID**: REQ-002 (tolerant `dedup_state` parsing in the transport)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `scripts/shared/http_transport.py`, `tests/shared/test_http_transport.py`