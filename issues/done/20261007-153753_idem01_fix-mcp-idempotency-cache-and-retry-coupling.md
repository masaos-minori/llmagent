# Fix MCP idempotency cache and retry coupling

## Priority
High

## Summary
Make the MCP idempotency cache serve only its intended purpose (suppressing duplicate execution of a re-sent logical call) and make the Agent-side retry and the server-side cache work together, so that side-effecting tools are neither silently skipped nor executed twice.

## Background
Source: local investigation notes (memo1.md, ISSUE-01); new finding, not yet registered as a Known Issue. The HTTP MCP transport retries failed calls, and the MCP server keeps a duplicate-detection cache for side-effecting tools. The two mechanisms were designed independently.

## Problem
- The Agent-side `HttpTransport.call()` does not send an `X-Idempotency-Key` header (Explicit in code — `scripts/shared/http_transport.py`: no occurrence of the header).
- The server-side context extraction falls back to an empty string when the header is absent, and `dispatch_tool()` tests `idempotency_key is not None`, so an empty string is treated as a valid key (Explicit in code — `scripts/mcp_servers/dispatch.py`, `scripts/mcp_servers/server.py`).
- Consequence (per investigation notes, not re-verified): the first side-effecting call is cached under the key `""`, and every later side-effecting call in the same server process returns that first result without executing, regardless of tool name or arguments.
- The cache has no TTL and no size bound, and it also caches error results and `dry_run` results.
- `HttpTransport` retries up to 3 times on 503 and on `httpx.RequestError` (including errors that can occur after the request was sent), without distinguishing write tools.

## Reason for Change
- Writes (git commit/push, file writes, `rag_delete_document`, etc.) can appear to succeed without being executed. This is the "report non-execution as success" failure that ADR-004 prohibits.
- A cached `dry_run` result can be returned as the response to a real execution.
- The unbounded cache grows without limit in a long-running server.
- Fixing only the cache would expose double execution on retry, so the cache fix and the retry fix must ship together.

## Implementation Intent
- The caller (Agent) owns key generation: one key per logical call, reused across retries of that call.
- A call without a key is never cached and always executes.
- The cache is keyed so that the same key with different content is rejected rather than served.

## Target Files or Areas
- `scripts/mcp_servers/dispatch.py`
- `scripts/mcp_servers/server.py`
- `scripts/shared/http_transport.py`
- `tests/mcp_servers/` (dispatch tests; the reason the defect went undetected is unconfirmed)

## Required Changes
- `dispatch_tool()`: when the key is `None` or empty, neither read nor write the cache.
- Key the cache by idempotency key plus tool name plus a normalized hash of the arguments; reject (as an error) a call that reuses a key with different content.
- Add a TTL and a maximum entry count with oldest-first eviction.
- Do not cache error results (`is_error=True`) or `dry_run=True` results.
- `HttpTransport.call()`: generate one UUID per logical call and send the same value as `X-Idempotency-Key` on every retry of that call.
- For write tools, allow retry after post-send errors (e.g. `ReadError`) only when an idempotency key is present.

## Constraints
- Preserve the existing wire format apart from the new header; the TTL and size bound are configuration or constants decided during implementation.
- Retry behavior for read-only tools must not change.
- ADR-004 (do not report non-execution as success) and ADR-007 (HTTP MCP) must remain satisfied.

## Acceptance Criteria
- Two consecutive write-tool calls without the header both execute (test).
- A re-sent call with the same key executes exactly once (test).
- A real execution after a `dry_run` call with otherwise identical input actually executes (test).
- Reusing a key with different tool name or arguments is rejected (test).
- Error results are not served from the cache (test).

## Testing Expectations
- Unit tests for `dispatch_tool()` cache behavior (empty key, same key, same key with different content, TTL expiry, eviction).
- Transport-level test that retries reuse the same key.
- Run the repository ruff, mypy, and targeted pytest suites.

## Documentation Impact
Update the MCP dispatch/transport documentation (idempotency ownership, retry rules, cache semantics) and ADR-004/ADR-007 references if their wording changes. Register the finding as a Known Issue until fixed (see the Known Issue ledger issue).

## Out of Scope
- Changes to git-mcp ref validation, audit records, or the RAG HTTP path.
- Redesign of the retry policy for read-only tools.
- Persisting the idempotency cache across server restarts.

## Dependencies
- Must be completed before the manual verification of the git-mcp ref-validation issue and the git-mcp audit issue, because their results cannot be trusted while this defect exists.

## Unresolved Questions
- Why the defect was not detected by existing tests (requires reading `tests/mcp_servers/test_dispatch*.py`).
- Concrete TTL and maximum entry count values.

## AI Implementation Instruction
Keep the change minimal and limited to the files above. Do not alter unrelated tools or retry policy. Add tests with the fix. If the existing tests contradict the intended semantics, stop and report instead of editing them silently.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-153811
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `scripts/mcp_servers/server.py`, `scripts/shared/http_transport.py`
