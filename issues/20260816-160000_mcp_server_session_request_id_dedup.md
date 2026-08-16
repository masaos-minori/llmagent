# Deduplicate `session_id`/`request_id` header-extraction boilerplate across `scripts/mcp_servers/**/*_server.py`

## Priority
Low

## Summary
The identical 4-line pattern —
`request.headers.get("x-session-id", "")` plus
`getattr(request.state, "request_id", request.headers.get("x-request-id", ""))` — is copy-pasted
verbatim in `call_tool()` across at least `git_server.py`, `mdq_server.py`, `github_server.py`,
`cicd_server.py`, `shell_server.py`, and `web_search_server.py`. This was independently observed
during separate, isolated refactor cycles on `git_server.py`, `web_search_server.py`, and
`shell_server.py` (2026-08-14 through 2026-08-16).

## Reason for Change
Six-plus-file duplication of the same request-context extraction logic is a maintenance risk —
any future change to session/request-id resolution semantics (e.g. adding a new header fallback)
requires updating every server file individually and risks drift between them. None of the
individual single-file refactor cycles could address this because each was explicitly scoped to
one file only.

## Implementation Intent
Add a shared helper (e.g. `extract_request_context(request) -> tuple[str, str]` or similar) to
`scripts/mcp_servers/server.py` (the existing shared base module for MCP servers) and have each
`*_server.py`'s `call_tool()` call it instead of inlining the extraction. Preserve the exact
current fallback order and default values (empty string, `request.state.request_id` before the
`x-request-id` header fallback) — this is a pure extraction, not a behavior change.

## Target Files or Areas
- `scripts/mcp_servers/server.py` (new shared helper)
- `scripts/mcp_servers/git/git_server.py`
- `scripts/mcp_servers/mdq/mdq_server.py`
- `scripts/mcp_servers/github/github_server.py`
- `scripts/mcp_servers/cicd/cicd_server.py`
- `scripts/mcp_servers/shell/shell_server.py`
- `scripts/mcp_servers/web_search/web_search_server.py`
- Unknown: confirm whether `scripts/mcp_servers/file/{delete,read,write}_server.py` and
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` have the same pattern (not
  confirmed during the cycles that raised this)

## Required Changes
- Write characterization tests asserting the exact `session_id`/`request_id` values extracted
  per affected server, for each header-present/header-absent/`request.state.request_id`-present
  combination, before touching any call site.
- Add the shared helper to `scripts/mcp_servers/server.py`.
- Replace each server's inline extraction with a call to the shared helper, one file at a time.

## Acceptance Criteria
- All affected `*_server.py` files call the same shared helper.
- Existing audit-log tests for each affected server pass unchanged (same `session_id`/
  `request_id` values recorded as before).
- No public route, response shape, or exception behavior changes.

## Testing Expectations
Full regression run of `tests/mcp_servers/` after the change; per-server audit-log tests must
show identical `session_id`/`request_id` extraction behavior before and after.

## Documentation Impact
None expected beyond noting the new shared helper if `docs/04_mcp_*` files enumerate
per-server request-context handling in detail (check before assuming no impact).

## Out of Scope
- Do not change the actual header names or fallback semantics.
- Do not touch unrelated logic in any of the affected `call_tool()` methods.

## AI Implementation Instruction
Confirm via `rg` which `*_server.py` files actually contain this exact pattern before touching
any of them — the list above is from partial, per-cycle observations, not an exhaustive search.
Add characterization tests per affected file before extracting, and validate each file
independently (one commit per file is acceptable) rather than one large multi-file commit.
