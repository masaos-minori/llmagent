# Move safety, approval, preview, and resource scope metadata into RuntimeTool

## Priority
High

## Summary
Make the RuntimeTool metadata discovered from MCP the base contract for safety tier, approval, preview support, and resource scope, and leave only environment-specific limits and stricter overrides in the Agent configuration. The same metadata carries the retry and reconciliation policy of a tool.

## Background
Source: consolidated `agent.toml` reduction backlog (`memo-issue.md`, Issue 3).

Evidence (`Explicit in code`, by `rg`): the maps `tool_safety_tiers`, `approval_risk_rules`, `approval_resource_keys`, and `plan_blocked_tools` are read in `scripts/agent/tool_policy.py`, the config builders, the production validator, and the field registry; `approval_dry_run_tools` is built in `scripts/agent/config_section_builders.py` (line 297) and the same capability is also coded as `_KNOWN_DRY_RUN_CAPABLE_TOOLS` in `scripts/agent/tool_approval.py` (line 56). That a tool must appear in both to be dry-run is from the backlog; so are the claims that resource scope for a branch depends on configuration and that audit rebuilds scope from masked arguments (`Needs confirmation`).

## Problem
Tool safety and approval decisions are spread over configuration maps, static constants, and RuntimeTool metadata. A change to an MCP server's tool can drift from the Agent's approval policy, and the large per-tool maps cannot be removed from `agent.toml`.

## Reason for Change
Security-sensitive behavior: approval risk, preview, and plan-mode blocking must follow the tool's real capability. It follows the exposure contract and the catalog consolidation, which it builds on.

## Implementation Intent
Tool-specific capability and structure belong to the RuntimeTool (base safety tier, side-effect class, approval tier, typed preview capability, typed resource keys). Deployment-specific restrictions belong to Agent policy as overrides that may only raise risk. Plan mode, approval, and audit read the same metadata. Missing or inconsistent metadata for a write tool is fail-closed at startup or preflight.

## Target Files or Areas
- `config/agent.toml`
- `scripts/shared/runtime_tool.py`, `scripts/shared/runtime_tool_registry.py`
- The MCP `/v1/tools` schema builders (`scripts/mcp_servers/server.py` and each server's tool schema; exact files `Unknown`)
- `scripts/agent/tool_policy.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_audit.py`, `scripts/agent/production_config_validator.py`
- `scripts/shared/tool_constants.py`, `scripts/shared/tool_routing_validation.py`
- `tests/agent/test_production_config_validator.py`, `tests/agent/test_tool_approval_risk.py`

## Required Changes
- Make base safety tier, side-effect class, and approval tier required RuntimeTool metadata.
- Represent preview capability as typed fields (for example `preview_supported`, `preview_side_effect_free`, `preview_required_for_high_risk`).
- Type each resource key (for example `filesystem_path`, `git_branch`, `github_repository`, `workflow_id`).
- Make a write tool with missing metadata fail-closed.
- Turn the full `tool_safety_tiers` and `approval_risk_rules` maps into overrides that may only raise risk; reject an override that lowers it unless a separately approved policy applies.
- Verify the Git write HIGH floor by operation class, not by a tool-name list.
- Remove `approval_dry_run_tools`, `_KNOWN_DRY_RUN_CAPABLE_TOOLS`, and `approval_resource_keys`; decide preview and resource scope from metadata; pass the canonical resource scope to audit.
- Keep `plan_blocked_tools` only as an exception denylist; decide plan mode from safety metadata.
- Replace the production validator's per-tool map checks with live metadata checks; keep static constants for drift detection only, and make a live-versus-static side-effect mismatch fatal.
- Add typed retry and reconciliation policy to RuntimeTool: `retry_policy` with the closed values `never`, `safe_read_retry`, `same_logical_call_only`, and `reconcile_then_retry`, plus `reconciliation_policy`, `idempotency_required`, and a policy version; an unknown or incomplete write tool defaults to no automatic retry and requires idempotency. Agent retry, approval, dispatcher, ledger, and recovery read this metadata, and the static retry sets (`RETRYABLE_TOOLS`) stay for drift detection only (source: the MCP deduplication backlog, `memo-issue.md`, Issue 3).

## Constraints
- A change to an ADR decision or invariant needs a maintainer approval record in the same change; do not write or simulate that approval.
- Metadata that is not present must fail closed; do not add a default that lowers risk.
- Follow the Current-Specification-Only policy: no compatibility reader for the removed maps.

## Acceptance Criteria
- [ ] `agent.toml` holds no per-tool safety, risk, dry-run, or resource-key map.
- [ ] Base approval decisions can be made from discovery metadata alone.
- [ ] Agent configuration keeps only protected paths, high-risk branches, allowed repositories, and explicit overrides.
- [ ] Plan mode, approval, and audit use the same metadata.
- [ ] Missing or inconsistent metadata fails closed at startup or preflight.
- [ ] Runtime retry and reconciliation decisions have one metadata source, and an unknown write tool is non-retryable and requires idempotency.

## Testing Expectations
- Missing and unknown safety tier; preview capability present, absent, and contract-violating; path, branch, and repository scope extraction; override that raises and one that lowers risk; plan-mode and approval-risk agreement.
- Run ruff, mypy, import-linter, and the affected tests.

## Documentation Impact
Yes. The metadata contract, the override rules, and the removed configuration keys.

## Out of Scope
- The exposure policy (issues/20261120-114209_agentcfg001_tool-policy-mode.md); the tool catalog source (issues/20261120-114210_agentcfg002_tool-catalog-registry.md); MDQ-specific tier values (`issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md`).

## Dependencies
- Depends on issues/20261120-114209_agentcfg001_tool-policy-mode.md and issues/20261120-114210_agentcfg002_tool-catalog-registry.md.
- Related: `issues/20261119-142129_mdqmcp007_mdq-approval-dry-run.md` sets the MDQ write tiers in `config/agent.toml`; if this issue lands first, those tiers belong in the MDQ tool metadata, and if it lands later, the values are moved. `issues/20261119-140512_mcpai005_structured-execution-context.md` defines execution mode and result metadata; the preview capability fields here must use its names. `issues/20261119-145306_cliplc008_mcp-health-capability.md` also extends RuntimeTool metadata; share one discovery schema version. `issues/20261120-115842_mcpdl003_dedup-config-isolation.md` removes the shared dedup configuration file and relies on this issue for the retry-policy authority; the `[retry_class]` mirror in `config/mcp_dedup.toml` is retired by the later of the two.

## Unresolved Questions
- `不明`: whether the MCP discovery schema can carry the new fields without a version change (needs the schema version definition).
- `不明`: preview field names, which must follow the shared metadata decided in `issues/20261119-140512_mcpai005_structured-execution-context.md`.

## AI Implementation Instruction
Write the fail-closed tests first. Never lower a risk by default. Do not write ADR approval statements. Stop and report if a server cannot publish the required metadata.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261120-114211
- **Related target files**: `config/agent.toml`, `scripts/shared/runtime_tool.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/mcp_servers/server.py`, `scripts/agent/tool_policy.py`, `scripts/agent/tool_approval.py`, `scripts/agent/tool_audit.py`, `scripts/agent/production_config_validator.py`, `scripts/shared/tool_constants.py`, `scripts/shared/tool_routing_validation.py`, `tests/agent/test_production_config_validator.py`, `tests/agent/test_tool_approval_risk.py`
