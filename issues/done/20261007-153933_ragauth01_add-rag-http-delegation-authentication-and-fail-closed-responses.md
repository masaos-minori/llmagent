# Add RAG HTTP delegation authentication and fail-closed responses

## Priority
High

## Summary
Bring the rag-pipeline MCP server and the Agent's RAG HTTP delegation under the same Bearer authentication as the other MCP servers, and make auth failures and error responses fail closed instead of falling back to local execution or being injected as retrieval context.

## Background
Source: local investigation notes (memo1.md, ISSUE-04), consolidating RAG-001, a finding that rag-pipeline-mcp has no authentication, and a finding that RAG responses' `is_error` is ignored. ADR-007 INV-09 and security_01 require Bearer authentication; ADR-004 and ADR-010 INV-04 forbid masking failures.

## Problem
- `rag_pipeline_server.py` does not call `attach_auth_middleware()`, so `/v1/call_tool`, `/rag_run_pipeline`, and `/rag_debug_pipeline` are callable without a token, including the destructive `rag_delete_document` (Explicit in code — `scripts/mcp_servers/rag_pipeline/` contains no `attach_auth_middleware` call).
- `call_rag_service()` sends `X-RAG-Token`, not the shared `Authorization: Bearer` header (Explicit in code — `scripts/rag/pipeline_service.py`).
- On 401/403 it logs "NOT falling back" yet returns `None`, and `augment()` treats `None` as "fall back to local execution" (RAG-001). This is latent today (no auth, so no 401) and becomes real once auth is added.
- Nothing sets `http_result_kind` to `"auth_error"`.
- The response `is_error` flag is not checked, so text such as "Tool disabled: ..." can reach the LLM as retrieval context. `selected_hits` is not part of the MCP response shape, so `fetch_result` is never set.
- The token comparison in `server.py` uses `==` instead of a constant-time comparison (Explicit in code — `scripts/mcp_servers/server.py` compares the Authorization header with `==`).
- Docstrings disagree with the implementation (empty-string fallback, "no cache hit", step numbering, a non-existent `_TIMEOUT` constant, `rag.toml` reference, duplicated endpoint list); `augment()` and `HttpAugment.run()` use `assert` for type validation.

## Reason for Change
- Missing authentication violates ADR-007 INV-09 and security_01; even on loopback, another local process can delete documents.
- Hiding authentication failure behind local execution masks token misconfiguration and revoked access (ADR-004, ADR-010 INV-04).
- Error text presented as retrieval results contaminates the evidence the answer is based on.
- A non-constant-time comparison does not meet the basic security requirement; `assert` is removed under `python -O` and cannot be used for runtime validation.

## Implementation Intent
- The RAG HTTP path uses the same Bearer mechanism as every other MCP server.
- The result type distinguishes success, empty result, authentication error, and transient failure; only transient failures may fall back.
- Authentication and the RAG-001 fix ship in the same release so RAG is never left broken in between.

## Target Files or Areas
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` and its config model (`auth_token`)
- `scripts/rag/pipeline_service.py`, `http_augment.py`, `augment.py`, `pipeline.py`
- `scripts/mcp_servers/server.py`
- `config/rag_pipeline_mcp_server.toml`, `config/agent.toml` (token and `rag_service_url` settings)
- security_01, ADR-007/ADR-010 related documentation

## Required Changes
- Attach `attach_auth_middleware(app, <auth_token>)` to the rag-pipeline server; add `auth_token` to its config model if missing.
- Send `Authorization: Bearer <token>` from `call_rag_service()`; remove `X-RAG-Token`.
- Introduce a dedicated result type (success / empty / auth error / transient failure); on auth error, `augment()` raises `RagPipelineError` without local fallback.
- Set `http_result_kind="auth_error"` in that case.
- Treat `is_error=True` responses as failures (fallback decided by kind).
- Stop depending on `selected_hits`; if needed, define it in the MCP response contract separately.
- Use `hmac.compare_digest` for the token comparison.
- Replace `assert` with explicit exceptions; fix the stale docstrings; make the 10-second request timeout a named constant.

## Constraints
- Authentication, the Bearer switch, and the fail-closed fallback change must be released together.
- Do not log tokens.
- Do not change the retrieval semantics for the success path.

## Acceptance Criteria
- A call without a token receives 401 (test).
- On 401 no local execution occurs and `http_result_kind` is `AUTH_ERROR`, verified through the caller's behavior (test).
- `is_error=True` responses are never used as context (test).
- Token comparison uses a constant-time function.

## Testing Expectations
- Unit tests for the result type and `augment()` branching; server auth middleware test; ruff, mypy, targeted pytest.

## Documentation Impact
Update security_01 (remove the rag-pipeline Known Deviation once fixed), ADR-007/ADR-010 related text, and the RAG HTTP delegation documentation. Known Issues RAG-001 and the new rag-pipeline authentication entry are removed from the ledger on completion.

## Out of Scope
- Changing RAG retrieval or ranking behavior.
- Other MCP servers' authentication.

## Dependencies
- None; internal tasks (auth, Bearer switch, fail-closed result type) must be released together.

## Unresolved Questions
- Whether `rag_service_url` and a token are set in `config/rag_pipeline_mcp_server.toml` and `config/agent.toml`, and whether HTTP delegation is used in production (affects urgency).
- The exact response shape used by the rag-pipeline tools (`rag_pipeline_service.py`, `rag_pipeline_models.py`, `rag_pipeline_tools.py` were not read).

## AI Implementation Instruction
Implement auth, Bearer switch, and the result type as one change. Do not add a fallback path for auth errors. Keep unrelated RAG code untouched. Stop and report if the response shape differs from the assumptions above.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-153933
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/rag/pipeline_service.py`, `scripts/rag/http_augment.py`, `scripts/rag/augment.py`, `scripts/rag/pipeline.py`, `scripts/mcp_servers/server.py`
