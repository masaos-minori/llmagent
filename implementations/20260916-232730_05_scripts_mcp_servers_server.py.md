## Goal

Extend `extract_request_context()` to also extract a new idempotency-key header, following the same pattern as the existing `request_id` extraction, for adoption by callers updated in the follow-up plan (Out-of-Scope).

## Scope

- Extend `extract_request_context()` in `scripts/mcp_servers/server.py` to also extract the new idempotency-key header
- No other files are modified in this row

## Assumptions

- The exact name of the idempotency-key header (e.g. `x-idempotency-key`, `x-tool-call-id`) is resolved during implementation against the actual caller data.
- The header extraction follows the same pattern as the existing `request_id` extraction: check `request.state.idempotency_key` first, then fall back to `request.headers.get("x-idempotency-key", "")`.
- The return value of `extract_request_context()` changes from `tuple[str, str]` to `tuple[str, str, str]` (adding the third element for the idempotency key).
- Callers that do not yet supply the idempotency key get today's unguarded behavior (no regression).

## Design decisions

- Adding the idempotency-key header extraction alongside the existing `request_id` extraction rather than replacing it: they serve different purposes; both must coexist.
- Using the same fallback pattern as `request_id`: check `request.state.idempotency_key` first, then fall back to `request.headers.get("x-idempotency-key", "")`.

## Alternatives considered

- Making the idempotency-key extraction mandatory — rejected: would break all existing callers that do not yet supply this value; opt-in defaults allow incremental rollout without breaking changes.

## Implementation

### Target file

`scripts/mcp_servers/server.py`

### Procedure

Extend `extract_request_context()` with the new header extraction.

### Method

1. Re-verify, immediately before editing, that each target row's cited line/content is unchanged since this Plan's evidence-gathering (per `rules/workflow-lifecycle.md` Revalidation): `scripts/mcp_servers/server.py` line 129, existing `request_id` extraction pattern (lines 136-140).
2. Change the return type of `extract_request_context()` from `tuple[str, str]` to `tuple[str, str, str]`.
3. Extract the idempotency-key header using the same pattern as the existing `request_id` extraction.
4. Return the idempotency key as the third element of the tuple.

### Details

```python
# Lines 129-140: extend extract_request_context():
# Before:
def extract_request_context(request: Request) -> tuple[str, str]:
    """Extract session_id and request_id from request headers/state.

    Returns:
        Tuple of (session_id, request_id), defaulting to empty string if not present.
    """
    session_id = request.headers.get("x-session-id", "")
    # request_id may be in state (set by middleware) or fall back to header
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    return session_id, request_id

# After:
def extract_request_context(request: Request) -> tuple[str, str, str]:
    """Extract session_id, request_id, and idempotency_key from request headers/state.

    Returns:
        Tuple of (session_id, request_id, idempotency_key), defaulting to empty string if not present.
    """
    session_id = request.headers.get("x-session-id", "")
    # request_id may be in state (set by middleware) or fall back to header
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    # NEW: idempotency_key may be in state (set by middleware) or fall back to header
    idempotency_key = getattr(
        request.state, "idempotency_key", request.headers.get("x-idempotency-key", "")
    )
    return session_id, request_id, idempotency_key
```

## Compatibility considerations

- The return type change from `tuple[str, str]` to `tuple[str, str, str]` will require callers to unpack three values instead of two. However, this is scoped out of this Plan (see Risks): six follow `extract_request_context()`, at least one (`file/write_server.py`) does not, and the remaining three were not yet confirmed either way during this Plan's Path B analysis.
- The idempotency-key header extraction uses the same fallback pattern as `request_id`: check `request.state.idempotency_key` first, then fall back to `request.headers.get("x-idempotency-key", "")`.

## Security considerations

- No security impact. This is adding a new header extraction, not changing any security boundary.

## Rollback considerations

- Reverting this change restores the original `extract_request_context()` signature and return value without the idempotency key. If needed later, the fields should be reimplemented to match the canonical exclude-and-FATAL duplicate-ownership policy from `McpToolDiscoveryService._dedupe_and_build()`.

## Validation plan

- Unit: run `uv run pytest tests/mcp_servers/test_mcp_server_base.py -q` to confirm no failures introduced, including new header-extraction test (AC-3, AC-5).
- Static analysis: `uv run ruff check scripts/mcp_servers/server.py`, `uv run mypy scripts/mcp_servers/server.py`.
- Import lint: `PYTHONPATH=scripts uv run lint-imports` to confirm no broken contracts introduced.

## Completion criteria

- `extract_request_context()` returns a three-element tuple `(session_id, request_id, idempotency_key)` (AC-3).
- The idempotency-key header extraction follows the same pattern as the existing `request_id` extraction (AC-3).
- All existing tests in `tests/mcp_servers/test_mcp_server_base.py` continue to pass without modification (AC-5).
- No new lint/type errors introduced.

## Out of scope

- Changes to `scripts/agent/tool_runner.py` — covered by separate row (REQ-001).
- Changes to `scripts/agent/shared/models.py` — covered by separate row (REQ-002).
- Changes to `scripts/agent/tool_audit.py` — covered by separate row (REQ-002).
- Changes to `scripts/mcp_servers/dispatch.py` — covered by separate row (REQ-003).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Change return type of extract_request_context() to tuple[str, str, str] | Pending | — | — | |
| 2 | Add idempotency-key header extraction | Pending | — | — | |
| 3 | Return idempotency_key as third element | Pending | — | — | |
| 4 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20260914-123621_arch02_tool-call-execution-id-idempotency-guard-missing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-135754_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-232730
- **Related target files**: scripts/mcp_servers/server.py
