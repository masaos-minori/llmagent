# Correct tool-routing documentation and remove obsolete compatibility claims

## Priority
High

## Summary
Some documentation states that `ToolRouteResolver` accepts `server_configs` for backward
compatibility. The current constructor no longer accepts that argument, and runtime route
resolution uses `RuntimeToolRegistry` as its sole authority with no fallback to static
`ToolRegistry`. `ToolExecutor.server_configs` remains an active execution dependency (MCP
server configuration, startup-mode checks, transport invocation, lifecycle behavior), and
static `ToolRegistry` remains active as an independent expected-ownership source for
configuration, live-discovery, and safety-tier drift validation. Documentation across several
files does not consistently distinguish these three.

## Background
`issues/done/20260828-130451_doc001_tool_route_resolver_stale_spec.md` already corrected the
stale `ToolRouteResolver(server_configs)` constructor example in
`docs/04_mcp_03_01_dispatch-and-routing.md` (and spot-checked `docs/04_mcp_03_02_tool-registry.md`).
This issue covers the remaining files that DOC-001 did not scope: it does not re-touch the
already-corrected constructor example, only the broader responsibility-split clarification
(`ToolExecutor.server_configs` vs. the removed resolver argument vs. static `ToolRegistry`'s
role) across the wider documentation set.

## Problem
Conflating runtime routing, MCP execution configuration, and static drift validation can cause
developers or AI agents to expect a resolver argument that no longer exists, or to classify
active validation/execution components as obsolete compatibility layers.

## Reason for Change
`ADR-003`'s fail-closed security rationale for unregistered tools depends on this
responsibility split being documented accurately and consistently across every file that
references it, not only the one file DOC-001 already corrected.

## Implementation Intent
Document the current responsibility split accurately: `RuntimeToolRegistry` is the sole
runtime-routing authority; `ToolRouteResolver` consults only `RuntimeToolRegistry` with no
legacy-route fallback for unknown tools; static `ToolRegistry` supplies expected ownership for
drift validation; `ToolExecutor.server_configs` is an active execution dependency; the former
`ToolRouteResolver.server_configs` argument is historical, not part of the current API.

## Target Files or Areas
- `docs/01_overview-arch-03-features.md`
- `docs/05_agent_13_reference-api.md`
- `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference.md`
- `docs/adr/ADR-003-runtime-tool-registry-routing-authority.md`
- Relevant Known Issues documents (`docs/04_mcp_90_inconsistencies_and_known_issues.md` and similar)
- `docs/04_mcp_03_01_dispatch-and-routing.md` — only for the broader `ToolExecutor.server_configs` distinction not covered by DOC-001, not the already-fixed constructor example

## Required Changes
- State that `RuntimeToolRegistry` is the sole runtime-routing authority, and that `ToolRouteResolver` has no fallback to static `ToolRegistry`.
- Document that unknown tool names fail resolution rather than using a legacy route.
- Clarify that `ToolExecutor.server_configs` is current MCP execution configuration, distinct from the removed `ToolRouteResolver.server_configs` argument.
- Describe static `ToolRegistry` as an expected-ownership source for drift validation; remove wording that presents it as an obsolete routing fallback.
- Select one canonical document for routing and registry responsibilities; replace duplicated explanations elsewhere with links to it.
- Move necessary history of the removed resolver argument to Change History.
- Update and close the related Known Issue entries after the documentation is corrected.

## Constraints
Documentation-only. Do not modify `ToolRouteResolver`, `RuntimeToolRegistry`, `ToolExecutor`,
or `ADR-003`'s Decision/Rationale/Invariants sections as part of this issue.

## Acceptance Criteria
- No current API reference documents a `ToolRouteResolver.server_configs` argument, in any of the files listed above.
- `ToolExecutor.server_configs` is clearly distinguished from the removed resolver argument, everywhere it is mentioned.
- Runtime and static registries have distinct and consistent documented responsibilities across all affected files.
- No current specification describes a static routing fallback.
- The canonical source for tool-routing responsibilities is explicit and cross-referenced from the other files.

## Testing Expectations
Not required — documentation-only change. Verify with
`uv run python tools/check_docs_quality.py` and `uv run python tools/check_docs_consistency.py --domain mcp`.

## Documentation Impact
Yes — this issue covers the documents listed above, extending
`issues/done/20260828-130451_doc001_tool_route_resolver_stale_spec.md`'s already-corrected
scope to the remaining files ADR-003's Migration Steps call for aligning.

## Out of Scope
- Removing static `ToolRegistry`.
- Changing runtime routing or tool-discovery behavior.
- Changing MCP server configuration.
- Re-editing `docs/04_mcp_03_01_dispatch-and-routing.md`'s constructor example already corrected by DOC-001.

## Dependencies
`issues/done/20260828-130451_doc001_tool_route_resolver_stale_spec.md` already corrected the
specific stale constructor example this issue's broader scope builds on.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Re-read `scripts/shared/route_resolver.py`, `scripts/shared/tool_executor.py`, and
`scripts/shared/runtime_tool_registry.py` before editing, to confirm the current responsibility
split rather than trusting this issue's restatement. Do not modify any file under `scripts/`.
If a document claim cannot be verified against current code, mark it `Needs Confirmation`
rather than guessing.
