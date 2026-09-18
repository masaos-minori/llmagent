# Wire idempotency-key header into each MCP server's route handler

## Priority
Medium

## Summary
Propagate the `x-idempotency-key` header from incoming requests through all ten MCP server route handlers to `dispatch_tool()`, enabling end-to-end duplicate detection for side-effecting tool calls.

## Background
REQ-003/REQ-004 added an opt-in duplicate-check mechanism to `scripts/mcp_servers/dispatch.py`'s `dispatch_tool()` and extended `scripts/mcp_servers/server.py`'s `extract_request_context()` to extract a new `idempotency_key` field. However, REQ-003 deliberately left wiring that header into each MCP server route-handler out of scope. The source Issue's Acceptance Criterion ("a retried side-effecting Tool Call... does not execute the underlying operation twice") remains only partially satisfied by the core-mechanism Plan alone.

## Problem
Without this follow-up, the idempotency-key mechanism ships but is inert: every one of the ten MCP server route handlers keeps calling `dispatch_tool()` with no `idempotency_key`, so the duplicate-check added by REQ-003 never actually fires for any live server, and a retried side-effecting Tool Call (file write, git operation, external API call) can still execute twice in production.

## Reason for Change
The idempotency guard is a correctness feature for side-effecting operations. Without propagation to all handlers, retry safety is broken and data integrity risks remain unaddressed.

## Implementation Intent
For each of the ten MCP server route-handler files:
1. Confirm whether the handler already calls `extract_request_context()` and how it uses the returned tuple.
2. For handlers that call `extract_request_context()` (Group A: 6 files): ensure the third return value (idempotency_key) is captured and passed to `dispatch_tool()`. Currently, six files call this helper but discard the third value:
   - `shell/shell_server.py:155`: `request_id, session_id, request_id = extract_request_context(request)` — third value overwrites `request_id`
   - `git/git_server.py:185`: same pattern
   - `mdq/mdq_server.py:81,343`: `request_id, session_id, _ = extract_request_context(request)` — discarded via `_`
   - `web_search/web_search_server.py:221`: same as shell/git
   - `cicd/cicd_server.py:119`: same as shell/git
   - `github/github_server.py:174`: same as shell/git
3. For handlers that do NOT call `extract_request_context()` (Group B: 4 files): additionally add `request: Request` parameter to the `call_tool` function signature (currently missing), then add the shared extraction call, capture the idempotency_key, and pass it to `dispatch_tool()`:
   - `file/read_server.py:279`: `async def call_tool(req: CallToolRequest)` — no `request` param
   - `file/delete_server.py:143`: same
   - `file/write_server.py:183`: same
   - `rag_pipeline/rag_pipeline_server.py:191`: same
4. Update the `_dispatch_*_tool()` helper signatures to accept an optional `idempotency_key: str | None` parameter and forward it to `dispatch_tool()`.

## Target Files or Areas
- `scripts/mcp_servers/shell/shell_server.py`
- `scripts/mcp_servers/git/git_server.py`
- `scripts/mcp_servers/mdq/mdq_server.py`
- `scripts/mcp_servers/web_search/web_search_server.py`
- `scripts/mcp_servers/github/github_server.py`
- `scripts/mcp_servers/cicd/cicd_server.py`
- `scripts/mcp_servers/file/read_server.py`
- `scripts/mcp_servers/file/delete_server.py`
- `scripts/mcp_servers/file/write_server.py`
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`
- `scripts/mcp_servers/dispatch.py` (signature update)

## Required Changes
- Add `idempotency_key: str | None = None` parameter to `_dispatch_*_tool()` in all ten files
- Pass `idempotency_key` to `dispatch_tool()` in all ten files
- Fix the three-value unpack bug in handlers using `extract_request_context()` (capture the third value as `idempotency_key` instead of reassigning `request_id`)
- Add `extract_request_context()` import and call in `file/read_server.py`, `file/delete_server.py`, `file/write_server.py`, and `rag_pipeline/rag_pipeline_server.py`
- Ensure the `/v1/call_tool` endpoint in each handler passes the request object to `extract_request_context()` where needed

## Constraints
- Must preserve existing public behavior when `idempotency_key` is absent (None or empty string should not trigger duplicate detection per `dispatch.py:116`)
- Must not change the audit logging signature or semantics
- Must not alter the FastAPI route registration or response model contracts

## Acceptance Criteria
- All ten MCP server route handlers pass the extracted `idempotency_key` to `dispatch_tool()`
- Handlers using `extract_request_context()` correctly capture the third return value as `idempotency_key`
- Handlers without `extract_request_context()` now call it and propagate the idempotency key
- No regression in existing functionality when `idempotency_key` header is absent
- Duplicate detection fires correctly when `x-idempotency-key` header is present on a retried side-effecting call

## Testing Expectations
- Unit tests verifying `dispatch_tool()` receives `idempotency_key` when present
- Integration test simulating a retried side-effecting call with same `x-idempotency-key` header
- Lint check (`uv run ruff check`) across all modified files
- Type check (`uv run mypy`) across all modified files

## Documentation Impact
Update any docstrings in `_dispatch_*_tool()` to reflect the new `idempotency_key` parameter. No user-facing documentation changes required.

## Out of Scope
- Adding the `x-idempotency-key` header to outgoing HTTP requests (not relevant for MCP server handlers)
- Modifying `dispatch.py`'s duplicate-detection logic itself (only wiring changes)
- Adding idempotency support to non-side-effecting tool calls beyond what `dispatch.py` already handles via `_is_side_effecting()`

## Dependencies
- Requires REQ-003/REQ-004 plan (`plans/done/20260916-135754_plan.md`) to be completed first
- Depends on `extract_request_context()` returning the correct three-tuple contract

## Unresolved Questions
- Do the four Group B servers (file/read, file/delete, file/write, rag_pipeline) currently have any other mechanism for tracking request context? If they use a different approach, the idempotency-key wiring must align with that existing pattern.

## AI Implementation Instruction
Do not rewrite unrelated files. Keep changes minimal: add the `idempotency_key` parameter to `_dispatch_*_tool()` signatures, wire it through to `dispatch_tool()`, fix the three-value unpack bug in `extract_request_context()` callers, and add extraction calls where missing. Preserve all existing imports, route registrations, and response models. Stop and report if requirements are unclear.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20260916-135754_plan.md
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260918-073838
- **Related target files**: scripts/mcp_servers/shell/shell_server.py, scripts/mcp_servers/git/git_server.py, scripts/mcp_servers/mdq/mdq_server.py, scripts/mcp_servers/web_search/web_search_server.py, scripts/mcp_servers/github/github_server.py, scripts/mcp_servers/cicd/cicd_server.py, scripts/mcp_servers/file/read_server.py, scripts/mcp_servers/file/delete_server.py, scripts/mcp_servers/file/write_server.py, scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py, scripts/mcp_servers/dispatch.py
