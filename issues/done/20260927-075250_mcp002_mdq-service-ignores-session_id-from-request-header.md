# MDQ service ignores session_id from request header

## Priority
Medium

## Summary
`tests/mcp_servers/mdq/test_mdq_exception_handlers.py::TestMdqServiceErrorHandler::test_session_id_from_header_and_request_id_from_middleware_state` expects the exception handler to use the `session_id` supplied in a request header (`'sess-456'`) but observes a freshly generated UUID instead, meaning the header value is not being read/propagated into the error response.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`assert '327d09a3-2231-4097-b808-e03647aa65f9' == 'sess-456'` — the exception handler's `session_id` field is a generated UUID, not the header-supplied value.

## Reason for Change
If a client provides a session-tracking header for debugging/correlation purposes, silently discarding it and generating a fresh UUID defeats request-correlation/tracing across a session, which affects debuggability of MDQ service errors.

## Implementation Intent
Read the MDQ service's exception handler to find where `session_id` is currently sourced (likely defaulting to a UUID generator) and where the request header is available (likely FastAPI `Request.headers`). Confirm the expected header name and wire it into the handler, falling back to UUID generation only when the header is absent.

## Target Files or Areas
- MDQ service exception-handler module (confirm exact path under `scripts/mcp_servers/mdq/`)
- `tests/mcp_servers/mdq/test_mdq_exception_handlers.py`

## Required Changes
- Read the header name the test sends (confirm exact header key from the test body).
- Update the exception handler to read `session_id` from that header when present, defaulting to UUID generation only when absent.

## Constraints
Preserve current behavior (UUID generation) when the header is absent — this is additive, not a replacement of the fallback.

## Acceptance Criteria
- The listed test passes.
- A case with no `session_id` header still falls back to UUID generation (confirm via existing or new test coverage).

## Testing Expectations
Run `tests/mcp_servers/mdq/test_mdq_exception_handlers.py`; run full suite once after the fix.

## Documentation Impact
N/A: unless the header-based session-id contract is meant to be documented for API consumers (Needs confirmation).

## Out of Scope
Other unrelated failing tests from the same full-suite run.

## Dependencies
N/A: none

## Unresolved Questions
Needs confirmation: the exact header name/key the test expects the handler to read.

## AI Implementation Instruction
Read the test's exact header-setup code first to confirm the header name before implementing. Keep the fallback-to-UUID behavior intact for the no-header case.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/mcp_servers/mdq/test_mdq_exception_handlers.py
