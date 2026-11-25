## Goal

Add the optional `dedup_state` field to `ToolCallResult` and accept it in `from_transport` (REQ-001, the result DTO cannot carry the dispatcher dedup outcome).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Sequencing: execute after the pending mcpai005 procedure `implementations/20261125-122426_02_scripts_shared_transport_dto.py.md`, which already appends `execution_mode` and `side_effect_applied` after `dispatch_stage`; re-read the file before editing and append `dedup_state` last (Plan Assumptions).
- All existing constructions use keywords and defaults, so a new defaulted field is source-compatible (Plan consumer scan).

## Design decisions

- `dedup_state` is an opaque `str` with `""` default (no dedup branch taken): `shared` is an import-linter leaf and must not import `mcp_servers` for the state vocabulary (Plan Design).
- No vocabulary validation on the DTO; the state set is owned by the server side (Plan Out-of-Scope).

## Alternatives considered

A shared enum or Literal state set was rejected: it would duplicate the server-side state set in `shared` and break on any future state value (REQ-002 forbids validation).

## Implementation
### Target file
`scripts/shared/transport_dto.py`
### Procedure
Add the dedup field to the result DTO and let `from_transport` accept it.

### Method
- Add `dedup_state` (new) as the last field of `ToolCallResult`: `dedup_state: str = ""`.
- Extend `ToolCallResult.from_transport` with an optional `dedup_state` keyword parameter defaulting to `""` and store it on the constructed result.

### Details
- Update the `ToolCallResult` docstring to state that `dedup_state` carries the dispatcher dedup branch as reported by the server, `""` when no branch applies.
- `dataclasses.replace` in `HttpTransport.call` and `ToolTransportInvoker` preserves the field automatically; no change here.

### Companion test files
- `tests/shared/test_transport_dto.py`
  - Procedure: add cases for the `""` default and for `from_transport` carrying a supplied `dedup_state` (REQ-001, AC-1).
  - Validation: `uv run pytest tests/shared/test_transport_dto.py`

## Compatibility considerations

Defaulted field only; records and results written before the change keep `""` (REQ-006). The 46 `ToolCallResult` consumers construct by keyword and are unaffected (Plan consumer scan).

## Security considerations

N/A: the field carries an opaque server-reported string, no credentials or free-text user content.

## Rollback considerations

N/A: revert the commit; the field is additive and defaulted.

## Validation plan

- `uv run pytest tests/shared/test_transport_dto.py tests/shared/test_tool_transport_invoker.py`
- `uv run mypy scripts/shared/transport_dto.py`
- `uv run ruff check` and `uv run ruff format`

## Completion criteria

- `ToolCallResult` exposes `dedup_state` as the last field with default `""`.
- `from_transport` accepts and stores it; existing DTO tests pass unchanged.

## Out of Scope

- Parsing the value from HTTP responses (row 2, `scripts/shared/http_transport.py`).
- Defining or validating the dedup state set (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261125 | Execute after the mcpai005 procedure on the same file Step 3a verified: field absent, append last; mcpai005 row already landed |
| 2 | Add the companion test per Validation plan | Completed | — | 20261125 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261125 | 51 passed; mypy/ruff clean |

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
- **Requirement ID**: REQ-001 (result DTO carries `dedup_state`)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `scripts/shared/transport_dto.py`, `tests/shared/test_transport_dto.py`