# Fix MCP subprocess startup and health check handling

## Priority
Medium

## Summary
Make Agent startup decide by two axes (required vs non-required server, down vs degraded) as ADR-004 specifies, and settle one design for `/health` authentication shared by the Agent and the servers.

## Background
Source: local investigation notes (memo1.md, ISSUE-06), consolidating AGENT-004 and two earlier findings. ADR-004 Group 7 says a failing `required=false` server is disabled and startup continues.

## Problem
- `start_servers()` and `verify_health()` never consult `cfg.required`; a `required=false` server that fails to start stops the whole Agent after retries.
- `verify_health()` calls `/health` without an Authorization header, while the MCP auth middleware requires authentication on all paths including `/health`, so servers with an `auth_token` should answer 401 (per investigation notes, not re-verified).
- A 503 from `/health` (degraded, e.g. rag-pipeline with `embed_url` unset) is treated as a startup failure.

## Reason for Change
- The implementation contradicts ADR-004 Group 7.
- If health checks and authentication do not mesh, correctly configured servers fail to start; conversely, if startup currently succeeds, authentication may be disabled somewhere. Either case needs resolution.
- Not distinguishing degraded from down lets a non-essential feature stop the entire Agent.

## Implementation Intent
- Decide startup outcome by "required or not" and "down or degraded", consistent with ADR-004.
- Choose a single `/health` authentication policy and align both sides.

## Target Files or Areas
- `scripts/agent/startup_mcp_starter.py`
- `scripts/shared/mcp_config.py`, lifecycle management (`start_http_subprocess`), `scripts/agent/shared/retry_helper.py` (to be read)
- `config/agent.toml`; ADR-004, ADR-007, adr-index INV-09

## Required Changes
- On startup or health failure, check `cfg.required`; for `required=false`, disable the server (`is_disabled`, removed from routing), log WARNING, and continue.
- Decide the `/health` authentication policy: Option A, exempt `/health`; Option B, the Agent sends Bearer. Recommended: Option B, consistent with ADR-007 "authenticate all endpoints".
- Parse the 503 body; when `liveness=true` and degraded, treat it as "started, partially available".

## Constraints
- Required servers must still fail startup when down.
- Do not weaken authentication to make the check pass.

## Acceptance Criteria
- A failing `required=false` server leaves the Agent running with that server's tools removed from routing (test).
- The startup health check succeeds against a server with `auth_token` set (test).
- A degraded-but-live 503 does not abort startup (test).

## Testing Expectations
- Unit tests for the starter's decision matrix; integration test against a server with auth; ruff, mypy, targeted pytest.

## Documentation Impact
Update ADR-004 Known Deviations (AGENT-004 until fixed), adr-index INV-09 status, and the startup/health documentation describing the chosen `/health` policy.

## Out of Scope
- Health endpoint changes of unrelated servers; circuit-breaker behavior.

## Dependencies
- The Known Issue ledger issue (ADR-004 Known Deviations and adr-index INV-09).

## Unresolved Questions
- Which servers start with `startup_mode=subprocess`, their `required` values, and whether a 401 actually stops startup today.

## AI Implementation Instruction
Do not change authentication to pass the check. Read the unread files listed above before designing. Keep the change confined to startup logic and the agreed health policy.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154014
- **Related target files**: `scripts/agent/startup_mcp_starter.py`
