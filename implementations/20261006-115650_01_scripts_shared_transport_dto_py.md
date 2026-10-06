## Goal

Restore `error_type="tool" if is_error else ""` in `ToolCallResult.from_transport()` and update its docstring to describe it builds a tool-level result from a successful transport response. (REQ-001 / REQ-002 / AC-4)

## Scope

- Change line 29: `error_type="transport" if is_error else ""` → `error_type="tool" if is_error else ""`
- Update the docstring (line 22): "Construct a ToolCallResult with default server_key and error_type." → describe tool-level result from successful transport response

## Assumptions

- Option A is the adopted policy (issue recommendation)
- The single caller (`HttpTransport._parse_http_response()`) needs `"tool"` and no caller needs `"transport"`
- Changing only the literal expression and docstring does not alter `from_transport()`'s signature or the `ToolCallResult` public contract

## Design decisions

- Adopt Option A: restore the pre-`3526dcc44` state the docs and tests were written against
- A constructor default of `"transport"` that every caller must override is a trap; restoring `"tool"` makes the default correct for the only use

## Alternatives considered

- Option B: keep `"transport"` as the default and override in `HttpTransport._parse_http_response()` with `dataclasses.replace(..., error_type="tool" if is_error else "")` — rejected because it leaves a constructor whose default is wrong for its only use and adds an override every future caller must remember

## Implementation

### Target file

`scripts/shared/transport_dto.py`

### Procedure

1. Change line 29 from `error_type="transport" if is_error else ""` to `error_type="tool" if is_error else ""`
2. Update the docstring (line 22) to state it builds a tool-level result parsed from a successful transport response and that transport failures are produced by the invoker

### Method

- Edit the two lines directly
- Verify no test asserts the old `"transport"` default before merging

### Details

**Before (line 22):**
```python
        """Construct a ToolCallResult with default server_key and error_type."""
```

**After:**
```python
        """Build a ToolCallResult from a successful transport response.

        This method is used for HTTP 200 responses carrying is_error: true
        (i.e., tool-level errors). Transport failures are produced by the
        invoker via _error_result(..., error_type="transport"), not here.
        """
```

**Before (line 29):**
```python
            error_type="transport" if is_error else "",
```

**After:**
```python
            error_type="tool" if is_error else "",
```

## Compatibility considerations

- Consumers of `error_type`: `tool_runner.py` (audit log line 152, diagnostics lines 159-162), `ToolTransportInvoker._record_success()` (counter line 154)
- No retry logic, scheduler, or health registry reads `error_type`
- Health state is unaffected because `_record_success()` calls `record_success()` regardless of `error_type`
- Both options produce identical runtime behavior; A localizes the classification in the DTO constructor rather than the caller

## Security considerations

- This change restores the correct `error_type` classification for HTTP tool-level errors
- Any external consumer of the `tool_exec` audit log that was adapted to `"transport"` after `3526dcc44` would see `"tool"` again — enumeration this session found no such consumer outside `scripts/`

## Rollback considerations

- Reverting to `"transport"` would restore the regression: tool-level errors misclassified, `stat_tool_errors` not incremented
- If audit-tooling adaptation exists, coordinate with its owner before reverting

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/shared/transport_dto.py` | Unit: `from_transport()` classification | `.venv/bin/python -m pytest tests/shared/test_transport_dto.py -q -p no:cacheprovider -p no:randomly` | `is_error=True` → `"tool"`, `is_error=False` → `""`, `source=="mcp"`, `server_key==""` |
| `scripts/shared/http_transport.py` (via integration) | Integration: HTTP 200 `is_error: true` path | `.venv/bin/python -m pytest tests/integration/test_robustness_chaos.py tests/integration/test_agent_mcp_integration.py -q -p no:cacheprovider -p no:randomly -k "a05 or 3b2 or 3b3"` | 3 tests pass; `error_type == "tool"` and `stat_tool_errors` incremented |
| `scripts/shared/tool_transport_invoker.py` | Integration: counter impact | Same regression command; `stat_tool_errors`/`stat_transport_errors` observed via existing assertions | Tool errors counted in `stat_tool_errors`; transport errors in `stat_transport_errors` |
| Full suite | Regression: no new failures | `.venv/bin/python -m pytest tests/agent tests/shared tests/integration -q -p no:cacheprovider -p no:randomly` | No new failures vs baseline (stp001/apr001 failures may remain) |

## Completion criteria

- Line 29: `error_type="tool" if is_error else ""`
- Docstring (line 22): describes tool-level result from successful transport response
- Three integration tests pass (AC-1/AC-2/AC-3)
- No new failures in full regression command (AC-5)

## Out of scope

- Changing the `error_type` vocabulary ("transport" | "tool" | "")
- Changing `server_key` handling (`from_transport()` keeps `server_key=""`; the `dataclasses.replace(parsed, server_key=self._server_key)` override in `HttpTransport.call()` stays)
- Changing the transport error path (`_error_result(..., error_type="transport")`, `_record_transport_error()`, `_handle_lifecycle_error()`)
- Changing retry logic or health tracking in `HttpTransport` / `ToolTransportInvoker`
- Modifying any existing test or documentation file
- Renaming or re-scoping `from_transport()`; redesigning `ToolCallResult`
- Deploying the `/opt/llm/scripts/` copy (deployment step only — no direct edit of the deployed copy)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Restore `error_type="tool"` in `transport_dto.py:29` | Pending | — | — | REQ-001 |
| 2 | Update `from_transport()` docstring | Pending | — | — | REQ-002 |
| 3 | Add or update tests per Validation plan | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20261005-121408_trn001_http-tool-level-errors-are-reported-with-error_type-transport-instead-of-tool.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261005-224839_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-115650
- **Related target files**: scripts/shared/transport_dto.py
