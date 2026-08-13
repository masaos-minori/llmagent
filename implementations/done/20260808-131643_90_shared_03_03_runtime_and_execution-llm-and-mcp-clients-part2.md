## Goal

Rebuild the shared/LLM/MCP clients chapter by compressing or removing implementation details such as full constructor signatures and mechanical error-type enumerations while explicitly preserving: LLMClient's HTTP/retry/SSE/error-classification responsibilities, the operational meaning of LLMTransportError, retryable-vs-fatal judgment criteria, partial_text handling responsibility delegation to agents, McpServerConfig as shared contract for MCP server connection settings, HealthRegistry support for MCP transport availability judgment, and load_all() boundary reading only agent.toml.

## Scope

**In-Scope**: `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md` structure change only.

**Out-of-Scope**: Other shared/db related chapters (`docs/90_shared_*.md`), source code changes, tests.

## Assumptions

- `memo-doc-shared-review.md` is valid and this chapter should be maintained as the authoritative reference for LLM/MCP common client boundaries.
- This chapter focuses on design intent, not implementation details.
- Existing internal links and cross-references must remain valid after editing.

## Design decisions

- Compress full constructor signatures into high-level parameter categories (e.g., "retry parameters", "SSE parameters").
- Replace mechanical error-type enumeration with "error classification categories".
- Retain explicit responsibility boundaries between LLMClient and agent layers.

## Alternatives considered

- Full removal of all constructor details: rejected because retry/SSE configuration semantics become unclear without any concrete anchors.
- Keeping full constructor signatures: rejected because they drift from reality as parameters evolve and add noise to the overview.

## Implementation

### Target file

`docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md`

### Procedure

1. Read current chapter content.
2. Identify full LLMClient constructor signature and replace with high-level parameter categories (retry params, SSE params, streaming callbacks).
3. Compress/remove mechanical full enumeration of error types — replace with "error classification categories" referencing `HTTP_STATUS_RETRYABLE`, `HTTP_STATUS_FATAL`, etc.
4. Compress/remove complete statistics attribute lists — replace with "instance-level counters for retries, reconnects, heartbeat timeouts, parse errors".
5. Compress/remove apply_config target field complete lists — replace with "hot-reload fields: temperature, max_tokens, retry config, SSE config".
6. Compress/remove McpServerConfig field descriptions — retain only ownership assertions.
7. Compress/remove comprehensive enum value tables — replace with "TransportType, StartupMode, SecurityProfile enums exist".
8. Compress/remove execution-flow pseudo-code — replace with high-level flow description.
9. Verify preservation of: shared-side LLMClient responsibility, detailed SSE design delegated to agent doc, LLMClient handles HTTP communication/retry/SSE/error classification, LLMTransportError operational meaning, retryable-vs-fatal judgment criteria, partial_text handling is agent responsibility, McpServerConfig is shared contract for MCP server connection settings, HealthRegistry supports MCP transport availability judgment, load_all() reads only agent.toml.
10. Validate all internal Markdown links and cross-references.
11. Confirm compliance with `memo-doc-shared-review.md` §「修正後の章構成テンプレート」.

### Method

Document compression via selective deletion of exhaustive constructor signatures, error-type enumerations, and statistics attribute lists while retaining structural responsibility declarations that point to source modules.

### Details

- **Preserve**: shared-side LLMClient responsibility, detailed SSE design delegated to agent doc (§10 references 05_agent_05_llm-and-streaming-part1.md), LLMClient handles HTTP communication/retry/SSE/error classification, LLMTransportError operational meaning, retryable-vs-fatal judgment criteria (HTTP_STATUS_RETRYABLE vs HTTP_STATUS_FATAL), partial_text handling is agent responsibility, McpServerConfig is shared contract for MCP server connection settings, HealthRegistry supports MCP transport availability judgment, load_all() boundary reads only agent.toml.
- **Compress/remove**: LLMClient full constructor signature → replace with "constructor accepts retry params (max_retries, retry_base_delay), SSE params (sse_heartbeat_timeout, sse_malformed_retry, sse_reconnect_max), streaming callbacks (on_token, on_usage), and hot-config fields"; error-type mechanical full enumeration → replace with "errors classified by kind: HTTP_STATUS_RETRYABLE, HTTP_STATUS_FATAL, CONNECT_ERROR, READ_TIMEOUT, HEARTBEAT_TIMEOUT, MALFORMED_SSE_FRAME, UTF8_PARTIAL_DECODE_ERROR, PREMATURE_EOF, UNKNOWN_STREAM_ERROR"; statistics attribute complete list → replace with "instance-level counters: stat_retries, stat_reconnects, stat_heartbeat_timeouts, stat_parse_errors"; apply_config target field complete list → replace with "hot-reload fields: temperature, max_tokens, max_retries, retry_base_delay, SSE config fields"; McpServerConfig field descriptions → compress to "fields validated in __post_init__: transport, url, cmd, startup_mode, tool_names, auth_token"; comprehensive enum value table → replace with "enums: TransportType, StartupMode(none/persistent/subprocess), SecurityProfile(local/production), HealthState(HEALTHY/DEGRADED/UNAVAILABLE)"; execution-flow pseudo-code → replace with "config loading: build_agent_config() → ConfigLoader.load_all() reads agent.toml; tool execution: ToolExecutor.execute → health gate → cache → raw MCP call".
- **Verify**: cross-references to `scripts/shared/llm_client.py`, `scripts/shared/mcp_config.py`, `scripts/shared/mcp_health.py` exist; agent doc reference for SSE design exists; retryable/fatal criteria clear; partial_text handling is agent responsibility clear; internal Markdown links valid; template compliance.

## Compatibility considerations

N/A — document-only phase.

## Security considerations

N/A — document-only phase.

## Rollback considerations

N/A — document-only phase.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Shared Side Llm Client Responsibility | Manual | Explicitly preserved |
| Detailed Sse Design Delegated To Agent Doc | Manual | Explicitly preserved |
| Llm Client Handles Http Communication Retry Sse Error Classification | Manual | Explicitly preserved |
| Llm Transport Error Operational Meaning | Manual | Explicitly preserved |
| Retryable Vs Fatal Judgment Criteria | Manual | Explicitly preserved |
| Partial Text Handling Is Agents Responsibility | Manual | Explicitly preserved |
| Mcp Server Config Is Shared Contract For Mcp Server Connection Settings | Manual | Explicitly preserved |
| Health Registry Supports Mcp Transport Availability Judgment | Manual | Explicitly preserved |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope

Other shared/db related chapters, source code changes, tests.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-233625_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-131643
- Related target files: 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md
