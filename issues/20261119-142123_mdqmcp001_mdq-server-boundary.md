# Unify MDQ server dispatch, public errors, audit redaction, health, and startup configuration

## Priority
High

## Summary
Create one fail-closed MDQ server boundary for tool availability, dispatch, public error responses, audit emission, configuration startup, authorized statistics, and non-sensitive health reporting.

## Background
Source: consolidated MDQ MCP backlog (`memo-issue.md`, Issue 1). Related archived work: `issues/done/20261018-191517_mcp002_mdq-mcp-server-lacks-pre-bind-fail-closed-security-posture-gate.md`, `issues/done/20261029-012525_ebrev001_mdq-config-loader-exception-mismatch.md`, `issues/done/20261026-220730_mcp003_mdq-auth-token-import-time-no-validation.md` (re-verify against them).

Evidence (`Explicit in code`, by reading and `rg`): `mdq_service.py:345-360` builds stats from `SELECT key, value FROM index_state` and prints the whole metadata dict without filtering to `allowed_dirs`; `health_check.py:145-153` puts the absolute database path into health details and dependency text; `mdq_tools.py` marks all tools `config_dependent: False`; `mdq_server.py:110` has a per-tool enabled function. The `/v1/call_tool` dispatch of a disabled tool, `grep_docs` discoverability, raw error text, and audit duplication claims are from the backlog and `Needs confirmation`.

## Problem
Discovery, execution, health, stats, error, and audit behavior are inconsistent: disabled tools may still execute, stats and health expose absolute paths and database-wide data, domain failures may return raw exception text, audit is emitted from two places, and raw queries, regular expressions, and absolute paths may be persisted.

## Reason for Change
Information disclosure and audit-integrity risk (security-sensitive); it blocks the search, indexing, and schema work that reuses the corrected contract.

## Implementation Intent
Every authenticated call: load one validated configuration, re-evaluate availability, validate and authorize, execute or reject, produce one safe structured result, and emit exactly one redacted audit record from a single `try/except/finally` boundary. Public health and stats expose only authorized, non-sensitive information; administrator diagnostics, if still required, live on a separate surface.

## Target Files or Areas
- `scripts/mcp_servers/mdq/mdq_server.py`, `mdq_service.py`, `audit_target.py`, `health_check.py`, `mdq_security_validation.py`, `mdq_models.py`, `mdq_tools.py`
- MDQ exception handlers and configuration loader; `config/mdq_mcp_server.toml`
- `tests/mcp_servers/mdq/` (existing: `test_mdq_health*.py`, `test_mdq_exception_handlers.py`, `test_mdq_error_taxonomy.py`, `test_mdq_config*.py`, `test_audit_target.py`; the backlog's `test_mdq_server.py`, `test_mdq_audit.py`, `test_mdq_disabled_tools.py`, `test_mdq_exception_audit.py` do not exist and are created here)
- Agent-side audit redaction helper shared with MDQ

## Required Changes
- One availability function used by `/v1/tools` and `/v1/call_tool`; disable path-dependent tools when `allowed_dirs` is empty and `grep_docs` when `enable_grep=false`; reject disabled tools before the handler with code `tool_disabled`, re-evaluated at call time; correct `config_dependent` metadata.
- Remove raw `index_state` from normal stats; restrict stats to canonical paths inside current `allowed_dirs`; reject stats when no roots are authorized; remove the absolute database path, global counts, and global timestamps from ordinary health; report readiness by non-sensitive state codes.
- Define stable error codes (validation, authorization, disabled tool, not found, database unavailable, consistency, timeout, unexpected) with one documented transport policy and retry guidance; never return raw exception text, SQLite details, or paths.
- Centralize audit emission; exception handlers only render transport; hash queries and regex patterns; remove previews; use authorized-root-relative identifiers or hashes for paths; persist path counts and root identities; one redaction helper for MDQ server and Agent audit.
- Load and validate production configuration once and share the result across service, authentication, health, and posture; missing production configuration is a pre-bind failure; defaults only in explicit development or test mode; strict booleans; no paths or secrets in startup errors.

## Constraints
- Authentication and malformed-HTTP behavior stay separate from domain-tool failures.
- Approval-display data stays separate from persistent audit data.
- Error-code and health-field changes may affect existing clients (`不明`).

## Acceptance Criteria
- [ ] A tool shown as disabled cannot be executed through HTTP or programmatic dispatch; `grep_docs` is disabled consistently when configured off.
- [ ] Normal stats and health expose no absolute source path, database path, or unauthorized-root count; shrinking the allowlist immediately removes prior-root information.
- [ ] Every authenticated call emits exactly one audit record.
- [ ] Queries, regex patterns, absolute paths, and raw exception text are absent from persistent logs and client responses.
- [ ] Every domain failure has a stable code and documented retry semantics.
- [ ] Missing production configuration fails before bind through one shared result.

## Testing Expectations
- Direct disabled-tool and stale-discovery calls; shared-database tests with authorized and unauthorized roots; stats and health leakage tests.
- Exactly-one-audit tests for success and every error class; redaction tests with customer names, secrets, regexes, and absolute paths; configuration precedence, missing configuration, and strict-boolean tests.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. The availability and execution contract; public health, authorized stats, and administrator diagnostics; the MDQ error-code table; audit redaction and exactly-one-record behavior; remove contradictory statements about disabled tools and exception handling.

## Out of Scope
- Search SQL and cancellation (`issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`); file processing results (`issues/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`); schema readiness (`issues/20261119-142128_mdqmcp006_mdq-fts5-schema-identity.md`).

## Dependencies
- Blocks `issues/20261119-142124_mdqmcp002_mdq-search-query-boundary.md`, `issues/20261119-142125_mdqmcp003_mdq-file-processing-outcomes.md`, and `issues/20261119-142130_mdqmcp008_mdq-schema-scope-consistency.md`.
- No open sibling issue or plan touches `scripts/mcp_servers/mdq/` (only archived work, listed above).

## Unresolved Questions
- `不明`: the transport policy for tool-domain failures (MCP tool error versus HTTP status).
- `不明`: whether an administrator diagnostic surface is still needed and how it is authenticated.
- `不明`: existing consumers of the current health and stats fields.

## AI Implementation Instruction
Write the leakage and exactly-one-audit tests first. Keep changes inside the MDQ server, its shared audit helper, and tests. Stop and report if the shared redaction helper changes other servers' audit output.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-142123
- **Related target files**: `scripts/mcp_servers/mdq/mdq_server.py`, `scripts/mcp_servers/mdq/mdq_service.py`, `scripts/mcp_servers/mdq/audit_target.py`, `scripts/mcp_servers/mdq/health_check.py`, `scripts/mcp_servers/mdq/mdq_security_validation.py`, `config/mdq_mcp_server.toml`
