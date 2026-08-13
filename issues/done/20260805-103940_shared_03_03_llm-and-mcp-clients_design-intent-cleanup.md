# Reduce implementation-derived detail in docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part{1,2}.md

## Priority
Medium

## Summary
Apply the design-doc reduction policy from `memo-doc-shared-review.md` to the LLM/MCP-clients chapter (both parts): keep `LLMClient`'s responsibility boundary and retryable/fatal error judgment; remove full constructor signatures and mechanical error-kind enumeration.

## Reason for Change
This chapter is the canonical source for the shared-layer LLM/MCP client boundary (per `memo-doc-shared-review.md` §「章間の正本ルール」: LLM/MCP共通クライアント境界 = `90_shared_03_03_runtime_and_execution-llm-and-mcp-clients`), but currently also carries full signatures and enum tables better left to code.

## Implementation Intent
Keep this chapter focused on `LLMClient`'s HTTP/retry/SSE/error-classification responsibility, that detailed SSE design is delegated to the Agent design doc, `LLMTransportError`'s operational meaning, and the config-boundary fact that `load_all()` reads only `agent.toml`.

## Target Files or Areas
- `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`
- `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md`

## Required Changes
- Keep: the shared-side `LLMClient`'s responsibility, that detailed SSE design is delegated to the Agent design doc, that `LLMClient` handles HTTP communication/retry/SSE/error classification, `LLMTransportError`'s operational meaning, the retryable-vs-fatal judgment criteria, that handling errors carrying `partial_text` is the Agent's responsibility, that `McpServerConfig` is the shared contract for MCP server connection settings, that `HealthRegistry` supports MCP-transport availability judgment, the config boundary that `load_all()` reads only `agent.toml`.
- Remove or compress: `LLMClient`'s full signature, a mechanical full enumeration of error kinds, a full list of statistics attributes, the full field list of `apply_config`'s targets, `McpServerConfig`'s field explanations, an exhaustive enum-value table, execution-flow pseudocode.

## Acceptance Criteria
- Both files follow the standard template from `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.
- No full signature, exhaustive enum table, or pseudocode flow remains.
- Retryable/fatal judgment criteria and the partial_text-handling-is-Agent's-responsibility statement remain explicit.

## Testing Expectations
Not required for behavior (documentation-only). No dedicated shared/db docs-consistency script exists; manually check internal links.

## Documentation Impact
This issue is itself a documentation-only cleanup task.

## Out of Scope
- Other `docs/90_shared_*.md` chapters.
- Any code under `scripts/shared/` (including `llm_client.py`, `mcp_config.py`, `mcp_health.py`).
- Detailed SSE design content that belongs in `docs/05_agent_05_llm-and-streaming*.md` (separate issue).

## AI Implementation Instruction
Follow `memo-doc-shared-review.md` §「90_shared_03_03_runtime_and_execution-llm-and-mcp-clients」. Do not edit code. Where detailed SSE design overlaps with the Agent doc set, point there instead of re-explaining. Mark unclear rationale as `Needs Confirmation`.

## Traceability
- Workflow phase: issue-creation
- Source: `memo-doc-shared-review.md` §「90_shared_03_03_runtime_and_execution-llm-and-mcp-clients」
- Generated at: 2026-08-05
