# Align MCP health, authentication, timeouts, degraded capabilities, and RuntimeToolRegistry metadata

## Priority
Medium

## Summary
Define one MCP health schema and authentication model, apply per-server timeouts, and connect degraded health to capability-level tool availability and explicit RuntimeTool metadata.

## Background
Source: consolidated CLI REPL and MCP lifecycle backlog (`memo-issue.md`, Issue 8). Related archived work: `plans/done/20261029-215111_toolhint001_dynamic-tool-health-hints.md`, `issues/done/20261029-104502_mcpgate001_mcp-mandatory-construction-contracts.md`.

Evidence (`Explicit in code`, by reading and `rg`): `scripts/agent/http_lifecycle_health_checker.py` accepts a response whose body has `liveness is True` as live (line 126) and has a timeout helper taking the smaller of the server health timeout and the startup timeout (lines 93-101); `scripts/agent/commands/cmd_mcp.py:276,325` prints `config_dependent` from each discovery row. Whether the health timeout is applied consistently, the zero-timeout semantics, the single-token authentication, and how `config_dependent` is derived (from status text per the backlog) are `Needs confirmation`; `scripts/agent/services/mcp_tool_discovery.py` and `mcp_health.py` exist.

## Problem
Per-server health timeout and authentication may be applied inconsistently; a 503 with `liveness=true` keeps every tool available even when only some capabilities work; RuntimeToolRegistry keeps construction-time availability with no safe dynamic update; diagnostics may infer configuration dependency from text.

## Reason for Change
Availability and diagnostic correctness after the configuration, launch, and process-state work; no data-loss risk.

## Implementation Intent
Health responses report liveness, readiness, degraded reason codes, and capabilities; authentication is explicit; request timeouts respect server and lifecycle deadlines; optional dependency loss disables only affected tools while required capability loss blocks startup; RuntimeTool diagnostics use explicit fields.

## Target Files or Areas
- `scripts/shared/mcp_config.py`, `scripts/agent/http_lifecycle_health_checker.py`, `http_lifecycle.py`
- MCP health DTO and schema; `scripts/agent/services/mcp_tool_discovery.py`, `mcp_health.py`
- `scripts/shared/runtime_tool.py`, `runtime_tool_registry.py`, `scripts/agent/commands/cmd_mcp.py`

## Required Changes
- Apply the effective per-server health timeout to startup and periodic checks; cap request timeout by the remaining lifecycle deadline; define or remove zero-means-unlimited; choose a one-token or distinct-health-token design (if distinct, a server-specific `health_auth_token` with secret registration and redaction).
- Add `liveness`, `ready`, degraded reason codes, and capabilities; distinguish optional from required dependency failure; do not treat `liveness=true` alone as readiness; fail startup when a required capability is missing; disable only the affected tools for optional capability loss.
- Add explicit `config_dependent` and capability dependencies to `RuntimeTool`, parsed strictly from discovery; keep status, configuration dependency, and health capability separate; rebuild and atomically swap a candidate registry when availability changes, or explicitly require restart; generate `/mcp status` from explicit metadata.

## Constraints
- Health tokens are secrets (redaction and registration).
- The health schema is shared with the MCP servers' health endpoints (`scripts/mcp_servers/`); coordinate field names there (`不明`).

## Acceptance Criteria
- [ ] Per-server timeout controls startup and periodic checks; health authentication follows one documented model.
- [ ] Optional dependency loss disables only dependent tools; required capability loss blocks startup.
- [ ] RuntimeTool diagnostics do not infer configuration dependency from status text.
- [ ] Registry changes are atomic.

## Testing Expectations
- Distinct and shared health-token cases; timeout and overall-deadline interaction; GitHub-token loss and other optional dependency failures; required dependency failure; candidate registry swap under active reads.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Health schema, authentication, capability semantics, and timeout rules.

## Out of Scope
- Launch and credential isolation (`issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`); process ownership (`issues/20261119-145305_cliplc007_mcp-process-ownership.md`); log redaction (`issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`).

## Dependencies
- Depends on `issues/20261119-145303_cliplc005_staged-reload-transaction.md`, `issues/20261119-145304_cliplc006_mcp-launch-spec-credentials.md`, and `issues/20261119-145305_cliplc007_mcp-process-ownership.md`. Blocks `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md` and `issues/20261119-145311_cliplc013_api-field-cleanup.md`.

## Unresolved Questions
- `不明`: one-token versus distinct health token (owner decision).
- `不明`: whether the registry will be swapped live or require restart.
- `不明`: how `config_dependent` is derived today.

## AI Implementation Instruction
Confirm how `config_dependent` is derived before changing it. Keep health semantics backward compatible where servers already report `liveness`. Stop and report the token-model decision instead of choosing silently.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-145306
- **Related target files**: `scripts/shared/mcp_config.py`, `scripts/agent/http_lifecycle_health_checker.py`, `scripts/agent/http_lifecycle.py`, `scripts/agent/services/mcp_tool_discovery.py`, `scripts/agent/services/mcp_health.py`, `scripts/shared/runtime_tool.py`, `scripts/shared/runtime_tool_registry.py`
