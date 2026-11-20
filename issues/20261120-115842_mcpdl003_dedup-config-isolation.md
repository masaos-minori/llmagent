# Replace the shared dedup configuration file with process-owned typed settings

## Priority
Medium

## Summary
Remove the standalone `config/mcp_dedup.toml`, give Agent call policy and MCP store settings to their own processes as typed configuration, and make every process using the shared store verify the same store-behavior fingerprint.

## Background
Source: consolidated MCP deduplication two-layer defense backlog (`memo-issue.md`, Issue 3, configuration part). The RuntimeTool retry, reconciliation, and idempotency policy of that item is carried by `issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`, which was updated to hold it.

Evidence (`Explicit in code`, by reading and `rg`): `scripts/shared/mcp_dedup.py` resolves `mcp_dedup.toml` through `resolve_config_dir()` (lines 85-90) and caches the parsed result in the module-level `_DEDUP_CONFIG_CACHE` (line 39); `scripts/mcp_servers/dispatch.py` loads it lazily on first use; `deploy/deploy.sh` (line 154) copies it into the shared deployed config directory; `scripts/shared/tool_constants.py` (lines 180-181) mirrors the retry classes so that the Agent does not import the file. Whether other MCP servers read the file, and how `scripts/agent/production_config_validator.py` uses it, are `Needs confirmation`.

## Problem
One file mixes Agent orchestration, shared-store operation, and tool-specific policy, and several processes must read a file that no process owns. Shared library code discovers platform configuration directly, which bypasses process configuration isolation.

## Reason for Change
Configuration ownership (ADR-002 config isolation). It is separate from the policy-authority change and can proceed once the store contract is fixed.

## Implementation Intent
The Agent reads only `agent.toml` for call policy. Each MCP process reads only its dedicated TOML for store settings. `mcp_dedup.py` receives immutable typed configuration at bootstrap, reads no platform file, and keeps no module-level cache. Settings that change shared-store semantics are fingerprinted, and a process whose fingerprint differs does not start.

## Target Files or Areas
- `config/agent.toml`, `config/mcp_dedup.toml`, and every `config/mcp_*.toml`
- `scripts/shared/mcp_dedup.py`, `scripts/shared/mcp_config.py`, `scripts/mcp_servers/dispatch.py`
- MCP process entry points and config builders (exact files `Unknown`)
- `deploy/deploy.sh`, service units, and container or volume mounts (`Unknown`)
- `scripts/agent/production_config_validator.py`

## Required Changes
- Add an Agent `[mcp_call]` section for logical id format, write-idempotency requirement, reconciliation enablement, approval grant lifetime, and mandatory state recording.
- Add a `[dedup]` section to each MCP server file that uses the store (enablement, database path, lease, retention, fail-closed behavior, identity requirement); define an immutable `DedupStoreConfig` and inject it at bootstrap.
- Reject invalid types, booleans used as integers, unknown fields, unsafe paths, and a missing section for a write-capable server.
- Remove directory discovery, TOML reading, and the module-level cache from `mcp_dedup.py`; remove `mcp_dedup.toml` and its deployment copy and mounts; enforce scope with `ConfigLoader.restrict_to()`.
- Fingerprint only shared-store behavior (database identity, schema version, lease, retention, fail-closed policy, identity requirement) and reject startup on mismatch; process-local settings may differ.

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change; do not write or simulate that approval.
- Follow the Current-Specification-Only policy: the old file is rejected, not read as an alias.
- Do not delete a TOML value only because it equals the code default (explicit deployment contract).

## Acceptance Criteria
- [ ] The Agent reads only `agent.toml` for call policy.
- [ ] Each MCP process reads only its own TOML; `mcp_dedup.py` does no configuration discovery.
- [ ] `mcp_dedup.toml` is neither read nor mounted.
- [ ] A shared-store semantic difference fails startup.

## Testing Expectations
- Process configuration isolation; strict parser and unknown-field validation; missing section for a write-capable server; cross-process fingerprint mismatch; deployment mount validation.
- Run ruff, mypy, import-linter, and the full test suite.

## Documentation Impact
Yes. Configuration ownership of the dedup settings and the removed file.

## Out of Scope
- RuntimeTool retry and reconciliation metadata (`issues/20261120-114211_agentcfg003_runtime-tool-metadata.md`); the store identity (issues/20261120-115841_mcpdl002_store-identity-continuity.md).

## Dependencies
- Depends on issues/20261120-115841_mcpdl002_store-identity-continuity.md for the fingerprint inputs.
- Related: `issues/20261119-141105_mcpdd001_dedup-keyless-config-gate.md` and `issues/20261119-140513_mcpai006_github-write-retry-policy.md` edit `config/mcp_dedup.toml`, which this issue removes; whichever lands later moves the settings. `issues/20261120-114212_agentcfg004_config-ownership-split.md` changes the same ownership model for other settings.

## Unresolved Questions
- `不明`: which MCP processes read `config/mcp_dedup.toml` today.
- `不明`: how the retry-class mirror is retired (depends on the RuntimeTool policy authority).

## AI Implementation Instruction
List readers of the file first and confirm them against source. Keep store behavior unchanged. Do not write ADR approval statements. Stop and report if a process still needs the removed file.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-115842
- **Related target files**: `config/agent.toml`, `config/mcp_dedup.toml`, `scripts/shared/mcp_dedup.py`, `scripts/shared/mcp_config.py`, `scripts/mcp_servers/dispatch.py`, `deploy/deploy.sh`, `scripts/agent/production_config_validator.py`
