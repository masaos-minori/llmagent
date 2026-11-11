# MCP security: server-side audit for dangerous writes and a dedicated MCP authentication ADR

## Priority
High

## Summary
Make every WRITE_DANGEROUS MCP tool leave a server-side audit record (starting with `rag_delete_document` in rag-pipeline-mcp, which writes none today), and define MCP authentication once in a new ADR that ADR-007 references and that all MCP documents agree with.

## Background
- Source: `memo-issue.md` items H-14 and M-08, re-checked against current source on 2026-11-09. Part of the memo is stale.
- `Explicit in documentation` (`docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`): eight servers write the shared audit log; file-read-mcp and rag-pipeline-mcp write none. `Explicit in code`: `scripts/mcp_servers/audit.py` is the shared audit helper; `scripts/mcp_servers/rag_pipeline/` has no audit emission (`rag_pipeline_security.py` mentions that calls are audited by the Agent). `Needs confirmation`: whether `rag_delete_document` is classified WRITE_DANGEROUS (the classification source was not located in this review).
- Memo claim refuted by current source: "`mcp_02_02` says only 4 servers refuse an empty token". `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` now says every HTTP MCP server must have a non-empty `auth_token`, including mdq-mcp; ADR-007 (`docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`) states the same in Decision 9; `require_auth_token` is used by every server module under `scripts/mcp_servers/`. `mcp_06_14_mcp-authentication-setup.md` now says a server refuses to start when the value is empty, and its Cause line says an empty token is rejected at startup; `Needs confirmation`: that no remaining sentence says "the server starts but health fails".
- `Explicit in documentation`: ADR-007 still lists "detailed implementation of security authentication (handled by a separate ADR)" as out of scope, and no such ADR exists under `docs/10_adr/`.
- The `accept_all_for_tests` bypass is handled by the non-strict removal issue in this batch.
- Related archived: `audit001_move-security-validation-to-each-mcp-server`, `mcp007_register-bearer-auth-in-shell-github-file-mcp-servers`, `mcp006_remove-the-loopback-health-admission-from-the-shared-auth-middleware` under `issues/done/`. Re-verify this issue against current source.
- Verification result (2026-11-11, adversarial check against current source):
  - `Confirmed by repository evidence`: `config/agent.toml` `[tool_safety_tiers]` classifies 14 tools as WRITE_DANGEROUS: `delete_file` and `delete_directory` (file-delete-mcp), `github_push_files`, `github_create_or_update_file`, `github_delete_file`, `github_create_pull_request`, `github_update_pull_request`, `github_merge_pull_request` (github-mcp), `rag_delete_document` (rag-pipeline-mcp), `trigger_workflow` (cicd-mcp), `git_checkout`, `git_pull`, `git_push` (git-mcp). A tool absent from the table also defaults to WRITE_DANGEROUS (`scripts/shared/runtime_tool.py`). The classification question is therefore resolved.
  - `Confirmed by repository evidence`: only `rag_delete_document` lacks a server-side audit record. file-delete-mcp, github-mcp, cicd-mcp, and git-mcp each call `_audit_log()` from their `call_tool` handler; `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py` `call_tool` calls no audit helper (it discards `session_id` and `request_id`).
  - `Confirmed by repository evidence`: the dependency on the non-strict removal is satisfied (`cad5e91ea`; `accept_all_for_tests` no longer appears under `scripts/`, `config/`, `tests/`, or `docs/`).
  - `Confirmed by repository evidence`: two sentences still contradict the all-servers rule: `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` troubleshooting "Missing secrets via environment variables" (Symptom "The server starts, but health checks fail"), and `docs/22_mcp/mcp_02_02_startup-modes-and-health.md` Bearer Authentication last bullet ("Empty server-side token (a standalone test run only): `attach_auth_middleware()` skips the authentication check"), whereas `attach_auth_middleware()` is fail-closed for an empty token (every request gets 401) and `require_auth_token()` aborts startup.
  - `Confirmed by repository evidence`: `docs/22_mcp/mcp_04_03_rag-pipeline-and-cicd.md` line 46 also says rag-pipeline-mcp has "no shared or dedicated audit log" and is missing from the issue's target list.
  - `Confirmed by repository evidence`: `governance_03` currently holds no Canonical Source Conflict entry, so there is nothing to close there; the ledger work belongs to the ledger issue.
  - `Confirmed by repository evidence`: the audit record (`AuditRecord` in `scripts/mcp_servers/audit.py`) has no `principal` field; the Bearer token is one shared secret per server, so the caller is identified only by `session_id` and `request_id`. "Principal" in Required Changes cannot be met without a format change that Constraints forbid.
  - `scripts/mcp_servers/audit.py`, `scripts/mcp_servers/dispatch.py`, and `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py` need no change (the helper is reused; dispatch already returns `DispatchResult.outcome`); they are reference files.
  - The next free ADR number is 017 (`docs/10_adr/adr_00_document-guide.md` records ADR-011 as deliberately unassigned).

## Problem
- A destructive RAG operation leaves a record only on the Agent side. If the Agent log is lost, or a caller other than the Agent reaches the server, a deletion leaves no trace and an incident cannot be reconstructed.
- MCP authentication rules (one shared variable per server, an empty token aborts startup, no bypass, restart required) live only in reference documents and in ADR-007's decision text; the documentation policy says reference documents cannot be the canonical source for decisions, and ADR-007 explicitly defers the details to an ADR that does not exist.

## Reason for Change
- Server-side audit of destructive writes is a security-sensitive gap; documents that point at a non-existent ADR make authentication rules unreviewable.
- Timing: depends on removing the test-only bypass first, so the new ADR can state "no bypass".

## Implementation Intent
- Every WRITE_DANGEROUS tool leaves a server-side audit record using the common audit format and success/failure semantics; rag-pipeline-mcp joins the audit-writing servers.
- MCP authentication is defined once in a new ADR; ADR-007 links to it and other documents defer to it.

## Target Files or Areas
- `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py`, `scripts/mcp_servers/audit.py`, `scripts/mcp_servers/dispatch.py`
- Tests under `tests/mcp_servers/` (an audit-line test per WRITE_DANGEROUS tool)
- A new ADR under `docs/10_adr/`, ADR-007, `docs/10_adr/adr_01_index.md`, `config/adr_authority.toml`
- `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`, `docs/22_mcp/mcp_06_05_reading-audit-logs.md`

## Required Changes
- Identify every WRITE_DANGEROUS tool and the server that hosts it, and record which of them lack a server-side audit record.
- Emit audit records in rag-pipeline-mcp using the common format (tool, target, principal, result, correlation ID) for success and failure.
- Add a test asserting an audit line for every WRITE_DANGEROUS tool on every server.
- Write a new ADR for MCP authentication (one shared variable per server on both sides, an empty token aborts startup on both sides, no bypass, changes take effect only on restart), link it from ADR-007, and register it in the index and authority model.
- Re-check `mcp_02_02` and `mcp_06_14` against the new ADR; correct any remaining contradictory sentence; close the corresponding Canonical Source Conflict entry in `governance_03` if one exists (see the governance-ledger issue).
- Update `mcp_02_03` and `mcp_06_05` so they no longer say rag-pipeline-mcp writes no audit log.

## Constraints
- Audit records must not contain secrets or file contents; use the existing masking and truncation conventions of `scripts/mcp_servers/audit.py`.
- A new ADR follows the ADR process and the authority model (`check_adr_authority.py`); approval records come from a maintainer, not the implementer.
- Do not change the Bearer-token mechanism itself; this issue documents and audits it.
- Keep the audit format stable for existing consumers (`mcp_06_05` log-reading procedures).

## Acceptance Criteria
- Server-side audit tests pass for all WRITE_DANGEROUS tools, including rag-pipeline-mcp's.
- No document contradicts the new authentication ADR; ADR-007 links to it.
- `check_adr_authority.py`, `check_adr_structure.py`, `check_docs_consistency.py --domain mcp`, and `check_docs_content_policy.py --strict` pass.

## Testing Expectations
- Unit tests for rag-pipeline-mcp audit emission (success and failure); a parametrized test over servers and their WRITE_DANGEROUS tools.
- `uv run pytest tests/mcp_servers -v`, then the full validation sequence from `rules/toolchain.md`.
- Documentation checkers listed above.

## Documentation Impact
- New ADR plus ADR-007, the ADR index, the authority registry, `mcp_02_02`, `mcp_02_03`, `mcp_06_05`, `mcp_06_14`. State intent, the authentication rules, and failure behavior; do not copy environment-variable values or tokens.

## Out of Scope
- Removing `accept_all_for_tests` and strict-mode toggles (non-strict removal issue in this batch).
- Adding authentication to non-MCP components (EventBus authentication is ADR-013).

## Dependencies
- Depends on: `issues/20261109-112640_adrrev004_non-strict-bypass-removal.md` (removal of `accept_all_for_tests`).
- Related, recently archived: `audit001`, `mcp007`, and `mcp006_remove-the-loopback-health-admission-from-the-shared-auth-middleware` under `issues/done/`.

## Unresolved Questions
- Resolved by verification: the WRITE_DANGEROUS list and the audit gap (only `rag_delete_document`); the remaining contradictory sentences (`mcp_06_14` troubleshooting, `mcp_02_02` last Bearer bullet).
- `Needs confirmation` (maintainer): whether the audit record must carry a principal. Until decided, the plan uses the existing fields only (`session_id`, `request_id`, `tool`, `target`, `outcome`, `server_key`, `error_type`).
- `Needs confirmation` (maintainer): the authority split for the new ADR (a new decision target for MCP authentication, and the narrowed ADR-007 supplemental limit under `mcp.technical-safety`).
- Maintainer approval is required for the new ADR and for the ADR-007 decision change.

## AI Implementation Instruction
- Start by listing WRITE_DANGEROUS tools and their audit status from code; do not rely on the memo's list.
- Reuse the shared audit helper; do not create a second audit format.
- Do not write approval records on a maintainer's behalf.
- Write documentation in English and follow the docs content policy; do not commit.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-113023
- **Related target files**: `scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py`, `scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py`, `scripts/mcp_servers/audit.py`, `scripts/mcp_servers/dispatch.py`, `config/adr_authority.toml`, `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`, `docs/10_adr/adr_01_index.md`, `docs/22_mcp/mcp_02_02_startup-modes-and-health.md`, `docs/22_mcp/mcp_02_03_audit-logging-and-errors.md`, `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md`, `docs/22_mcp/mcp_06_05_reading-audit-logs.md`
