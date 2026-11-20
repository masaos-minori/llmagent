## Goal

Delete `derive_idempotency_key`, send the logical call id as `X-Idempotency-Key`, and refuse to send any `call_tool` whose context carries no id (`REQ-003` transport key replacement, AC-1, AC-3).

## Scope
**Release unit**: contract-chain

## Assumptions
- The server treats the header opaquely (`server.py` middleware :149-180, `dispatch.py` `_duplicate_cache` :103-135) — no server-side change (Plan Assumption).
- The header key shape constraint `^[A-Za-z0-9_-]{1,64}$` is satisfied by a uuid7 string.

## Design decisions
- Delete `derive_idempotency_key` (:45-58; verified 2026-11-20) and the `uid`/auth-hash fallback (:198-201); the header value becomes `context.call_id` (:208 assignment site).
- A `call_tool` request with no context or an empty `call_id` is refused before any HTTP send, returning an error `ToolCallResult` (`error_type="routing"`, `dispatch_stage=""`) — this is the AC-3 gate at the wire boundary. Note: `call()` currently signals failures by raising; the refusal returns a result instead (the invoker records it as a transport-failure result with `dispatch_stage=""`).
- `X-Session-Id`/Authorization header construction (:204-207) stays unchanged.
- `TransportError` gains a `stage` attribute (resolved 2026-11-20, consumed by row 15/row 4, AC-6): set at each raise site — ambiguous write status raise (:228-236) and `HTTPStatusError` (:262-271) and parse `ValueError` (:272-275) → `"response"`; `TimeoutException` (:258-261) and the post-send `RequestError` gate (:287-292) → `"sent"`; pre-send safe-error exhaustion (:296-300) → `""`. Results returned by `call()` (:250-257) carry `dispatch_stage="response"`.

## Alternatives considered
- Keeping a derived key as fallback for context-less calls: rejected — it re-creates the identical-arguments collision AC-1 forbids.

## Implementation
### Target file
`scripts/shared/http_transport.py`

### Procedure
Remove the function; rewire the header block (:192-208) to the context; add the refusal branch ahead of the request loop (:210+ retry logic).

### Method
Refusal returns the same error-result shape the existing transport-error path builds; retries reuse the same `context.call_id` unchanged (retry-invariance, AC-1).

### Details
- Drop now-unused imports if `hashlib`/`json` lose their last user here (ruff `F401` gate).

### Companion test files
- `tests/shared/test_tool_executor_routing.py`
  - Procedure: delete `derive_idempotency_key` imports/assertions (import at :14; derived-key expectations also at :352-385 — the one-key-per-logical-call retry-reuse pin must be rewritten to assert the context's `call_id` is reused across retries); assert refusal when no context.
  - Validation: `uv run pytest tests/shared/test_tool_executor_routing.py` passes.

## Compatibility considerations
Server-side dedup keeps working on opaque keys; wire format unchanged (still a header string).

## Security considerations
No content-derived key leaks tool arguments into the wire key.

## Rollback considerations
N/A: revert the commit.

## Validation plan
`uv run pytest tests/shared/test_http_transport.py tests/shared/test_tool_executor_routing.py` (row 26 updates the transport tests).

## Completion criteria
`rg derive_idempotency_key scripts/` returns nothing; every outbound `X-Idempotency-Key` equals the call's logical id; id-less sends are impossible.

## Out of Scope
Executor/invoker threading (rows 14-15); server middleware (reference only, unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-11-21 | 2026-11-21 | `derive_idempotency_key` deleted; `call(name, args, context)`; header=context.call_id; context-less calls refused; `TransportError.stage` set at all raise sites |
| 2 | Add or update tests per Validation plan | Completed | 2026-11-21 | 2026-11-21 | covered by rewritten tests/shared/test_http_transport.py (row 26) + companion test_tool_executor*.py adaptation |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-11-21 | 2026-11-21 | ruff+mypy+tests/shared (1280 passed)+lint-imports (6 kept); interim `_derive_transport_key` bridge added to tool_runner.py until row 4 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-11-21 | 2026-11-21 | Docs sweep owned by mcpai012 |

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
- **Requirement ID**: `REQ-003`
- **Source issue**: `issues/20261120-115840_mcpdl001_approval-grant-intent.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261120-222144_mcpdl001_approval-grant-intent.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-225424
- **Related target files**: `scripts/shared/http_transport.py`, `tests/shared/test_tool_executor_routing.py`
