---
title: "ADR-013: MCP Tool Availability Model"
category: adr
status: proposed
date: "2026-08-21"
last_updated: "2026-08-21"
owners:
  - agent-team
reviewers:
  - architecture-reviewer
decision_scope:
  - mcp
  - agent
related: []
supersedes: []
superseded_by: null
---

# ADR-013: MCP Tool Availability Model

## Status

Proposed

Allowed values: `Proposed`, `Accepted`, `Rejected`, `Deprecated`, `Superseded`. Changing an Accepted decision requires a new ADR that supersedes this one, not an edit to this body.

## Summary

Tool existence, discovery, LLM visibility, routing ownership, static configuration availability, dynamic server health, approval state, and execution eligibility are distinct concepts that MUST NOT be collapsed into a single "enabled" flag. `RuntimeToolRegistry` is the sole runtime authority for ownership, routing, LLM-visible metadata, and scheduling metadata. Static availability (config-derived) and dynamic health (server reachability) are separate, unintegrated subsystems and MUST remain conceptually separate even where future work improves their coordination.

## Context

### Problem

The codebase currently mixes several availability-like concepts without consistent terminology or consistent enforcement: some MCP servers compute a per-tool `enabled`/`disabled_reason`, others do not; a documented "two-stage" filtering design turned out, on inspection, to have a no-op second stage; a `RuntimeTool.requires_approval` field is written but never read; and reload does not rediscover tools even though this is easy to assume otherwise. Left undocumented, these gaps invite future code to "fix" a stage that already does nothing, or to assume approval-gating exists somewhere it does not.

### Constraints

- Discovery (`McpToolDiscoveryService.discover_all()`) currently runs once, at agent startup, over HTTP `/v1/tools` calls to each configured server.
- `RuntimeToolRegistry` is an in-memory structure rebuilt only on agent process restart.

### Assumptions

- Target environment: single Agent process, multiple MCP server processes reachable over HTTP.
- Re-evaluate if: hot server addition/removal without agent restart becomes a requirement, or if per-server availability computation is centralized instead of being each server's own responsibility.

## Decision

### Decision Details

1. `RuntimeToolRegistry` remains the sole runtime authority for tool ownership/routing, LLM-visible metadata, execution-policy metadata, and DAG scheduling metadata. Static registries (`ToolRegistry`, `tool_constants.py`) validate drift only; they MUST NOT become alternative routing authorities.
2. The following concepts are distinct and MUST be referred to by name, not by an undifferentiated "enabled": Defined, Discoverable, Owned, LLM-visible, Statically available, Dynamically available, Routable, Approved, Executable.
3. Static availability (config-derived, computed by each MCP server and captured once at startup by `McpToolDiscoveryService`) and dynamic health (server reachability and circuit-breaker state, tracked continuously by `McpServerHealthRegistry`/`ToolExecutor`) are separate subsystems. Static availability governs LLM visibility and routing eligibility; dynamic health governs whether an already-routable call succeeds at execution time. A tool statically enabled but dynamically down remains LLM-visible and routable, and fails only at execution.
4. Approval requirement is not a form of disabled availability. It is owned by `agent/tool_policy.py`/`tool_approval.py`, operates after registry/routing resolution, and MUST NOT be represented as, or confused with, a disabled tool.
5. Duplicate ownership (the same tool name reported by two servers) MUST fail agent startup (`FATAL`, regardless of `security_profile`/`strict` settings), even though the registry-construction step itself excludes the duplicate rather than raising — the FATAL finding is what stops the process, not an exception from registry construction.
6. Reload (`/reload`) updates only policy-derived fields (`agent_safety_tier`, `requires_approval`, `enabled_for_llm`) via `apply_policy()`; it does not rediscover tools or refresh `raw_definition`/`disabled_reason`/`status`. A full agent process restart is required to reflect config changes that affect discovery-derived state. This is the accepted policy (equivalent to "Policy A: Configuration reload without rediscovery" as opposed to atomic rediscovery) until a future ADR adopts atomic rediscovery.
7. All MCP servers SHOULD converge on the same availability contract (`config_dependent`, `enabled`, `disabled_reason`); today `git`, `file_read`/`file_write`/`file_delete`, `github`, and `web_search` implement it, while `rag_pipeline`, `cicd`, `mdq`, and `shell` do not — tracked as Known Issue MCP-002, not treated as acceptable permanent divergence.

### Scope

- **Components**: `shared/runtime_tool.py`, `runtime_tool_registry.py`, `route_resolver.py`, `agent/services/mcp_tool_discovery.py`, all `scripts/mcp_servers/*/server.py` `/v1/tools` handlers.
- **Concepts**: static availability, dynamic health, LLM visibility, routing, approval — as defined in Decision Details #2.

### Out of Scope

- Redesigning approval policy itself (owned by `tool_policy.py`/`tool_approval.py`; referenced, not redesigned, here).
- Implementing `include_disabled`/`disabled_code` wiring (tracked as Known Issue MCP-001; this ADR documents the target contract those parameters already partially exist for).
- Adopting atomic rediscovery (Policy B) — this ADR records the current accepted policy (A) and notes B as a future option, not a decision made now.

## Rationale

### 1. Correctness

A single "enabled" concept that actually means up to five different things (defined/discoverable/owned/LLM-visible/statically-available) leads to code that checks the wrong one and to documentation (as found during this review) that describes a filtering stage which does not actually filter.

### 2. Maintainability

Making "static vs. dynamic" and "approval vs. disabled" explicit prevents a natural, low-cost mistake: implementing a health-driven feature by writing to the same field that governs LLM visibility, which would silently change what the LLM is offered based on transient server health.

### 3. Operability

Documenting that reload does not rediscover (rather than leaving it ambiguous) prevents operators from assuming a config change has already reached the live registry when only a full restart does.

## Alternatives Considered

### Alternative A: Unify static availability and dynamic health into one `enabled` signal

#### Advantages
Simpler mental model; one flag to check.

#### Disadvantages
Would require LLM-visible tool lists to change on every circuit-breaker trip, causing tool availability to flap from the LLM's perspective during transient network issues — a much larger blast radius than an execution-time error.

#### Reason for Rejection
The current separation (static governs visibility, dynamic governs execution-time success) is already the safer design; this ADR keeps it and makes it explicit rather than replacing it.

### Alternative B: Represent approval-required as a disabled state

#### Advantages
Reuses the existing disabled-tool machinery instead of a separate subsystem.

#### Disadvantages
Approval is a per-call, per-argument decision (e.g., risk escalation based on path or branch); a static "disabled" flag on the tool cannot express that, and collapsing the two would make approval-required tools invisible to the LLM when they should remain visible and simply gated at execution.

#### Reason for Rejection
Conflates a call-time policy decision with a tool-level availability flag; keeping them separate is both already the implemented reality and the correct model.

## Consequences

### Positive Consequences
- Shared vocabulary makes future MCP server work and future agent-side routing work harder to accidentally misuse.
- Explicit documentation of the reload/restart boundary prevents a plausible but wrong operational assumption.

### Negative Consequences
- None beyond documentation and terminology discipline — this ADR does not change runtime behavior.

### Operational Consequences
- Operators must restart the agent process for discovery-derived availability changes to take effect; `/reload` is insufficient for that class of change.

### Security Consequences
- Static availability continuing to gate LLM visibility (rather than being merged with dynamic health) keeps a config-driven security control (e.g., `read_only=true`) from being weakened by transient health signals.

## Invariants

- INV-01: `RuntimeToolRegistry` remains the sole routing/LLM-visibility/scheduling authority; static registries MUST NOT be used for routing decisions.
- INV-02: A statically disabled tool MUST NOT be exposed to the LLM as executable.
- INV-03: Dynamic health state MUST NOT alter `enabled_for_llm`/LLM-visible tool lists.
- INV-04: Approval-required state MUST NOT be represented as a disabled tool.
- INV-05: Duplicate tool ownership across servers MUST fail agent startup.

## Exceptions

None.

## Failure Policy

### Fail-Fast Conditions
- Duplicate tool ownership detected during discovery → agent startup FATAL.
- Missing required schema-2.0 discovery fields (`is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`) → tool excluded from the registry, not silently defaulted.

### Fail-Open or Degraded Conditions
- A server unreachable at startup has its tools excluded from the registry (LLM never sees them) rather than the agent refusing to start — this is a deliberate degraded-start allowance, not a violation of INV-05 (which concerns ownership conflicts, not unreachability).

### Retry Policy
- Dynamic health uses circuit-breaker CLOSED/OPEN/HALF_OPEN trial-recovery semantics at the execution layer; this is unchanged by this ADR.

### Fallback Policy
Not applicable.

## Data Ownership and Persistence

Not applicable in the DB sense — `RuntimeToolRegistry` is an in-memory, per-process structure rebuilt on restart; it is not persisted to disk.

## Verification

### Automated Tests
- **Test**: a tool statically disabled by config is absent from `llm_tool_definitions()` — **Verifies**: INV-02 — **Type**: Regression — **Blocking**: Yes
- **Test**: a circuit-open server's tools remain in `llm_tool_definitions()` — **Verifies**: INV-03 — **Type**: Integration — **Blocking**: Yes
- **Test**: duplicate tool ownership across two servers produces a FATAL startup outcome — **Verifies**: INV-05 — **Type**: Integration — **Blocking**: Yes (already covered per investigation)

### Manual Review
- Confirm no future PR re-merges the static/dynamic distinction by having a health-driven code path write to `enabled_for_llm`.

## Migration and Rollout

Existing implementation already satisfies INV-01, INV-03, and INV-05; INV-02/INV-04 are satisfied for the servers that implement `enabled`/`disabled_reason` and for the `requires_approval` separation, respectively. No migration is required; remaining work is closing MCP-001/MCP-002 (tracked separately), not changing this model.

### Compatibility
No API or schema compatibility impact — this ADR documents and constrains the existing model rather than changing field shapes.

### Rollback
Not applicable.

### Completion Criteria
This ADR moves to Accepted once the invariants are confirmed by the listed tests and the vocabulary in Decision Details #2 is reflected consistently across the MCP/agent documentation set.

## Implementation Notes

- Implementation files: `scripts/shared/runtime_tool.py`, `runtime_tool_registry.py`, `route_resolver.py`, `scripts/agent/services/mcp_tool_discovery.py`
- Key symbols: `RuntimeToolRegistry.resolve()`, `RuntimeToolRegistry.llm_tool_definitions()`, `RuntimeToolRegistry.tool_spec_for_call()`, `McpToolDiscoveryService.discover_all()`, `McpServerHealthRegistry`
- Corresponding tests: `tests/test_route_resolver.py`, `tests/test_tool_constants.py`, MCP discovery consistency tests referenced in `04_mcp_03_02_tool-registry.md`

## Known Deviations

- **Known Issue**: MCP-001 — `include_disabled`/`disabled_code` parameters exist but have no reachable caller.
- **Known Issue**: MCP-002 — `rag_pipeline`, `cicd`, `mdq`, and `shell` do not implement `enabled`/`disabled_reason`.

## Review Triggers

- Hot server addition/removal without a full agent restart becomes a requirement (would require adopting atomic rediscovery, Policy B).
- A future design centralizes availability computation instead of leaving it to each server.

## Approval

### Required Reviewers
- Architecture Owner

### Approval Record
- **Approved By**: pending
- **Approval Date**: pending

## Related Documents

### Specifications
- [Tool Runtime Availability Metadata](../04_mcp_03_06_tool-runtime-availability-metadata.md)
- [Tool Registry](../04_mcp_03_02_tool-registry.md)
- [Tool Call Dispatch Flow and Routing Resolution](../04_mcp_03_01_dispatch-and-routing.md)

### Known Issues
- MCP-001, MCP-002 in [MCP Known Issues](../04_mcp_90_inconsistencies_and_known_issues.md)

### Implementation References
- `scripts/shared/runtime_tool_registry.py` — `RuntimeToolRegistry`
- `scripts/agent/services/mcp_tool_discovery.py` — `McpToolDiscoveryService`

## Change History

- 2026-08-21: Created as Proposed.
