## Goal
- Restructure `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md` and `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md` to remove overly detailed constructor signatures, error enumerations, statistics attribute lists, apply_config target field lists, McpServerConfig field descriptions, exhaustive enum value tables, and execution flow pseudo-code while explicitly preserving why LLMClient has HTTP/retry/SSE/error classification responsibilities, why detailed SSE design is delegated to Agent design docs, LLMTransportError operational meaning, retryable vs fatal judgment criteria, why partial_text error handling is agent responsibility, McpServerConfig as shared contract for MCP server connection config, HealthRegistry supporting MCP transport availability judgment, load_all() reading only agent.toml config boundary.

## Scope
- **In-Scope**: 
  - `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
  - `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/runtime chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and these chapters should describe "why LLM/MCP client design decisions exist"
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (ToolExecutor section):
- Compress Section 9 ToolCallResult full dataclass listing (lines 29-37): replace with prose describing result contract categories (output, is_error, request_id, server_key, source, error_type)
- Compress Section 9 execute() sequential steps (lines 42-55): replace with prose describing execute behavior at conceptual level (cache check, stampede protection, routing resolution, health gate, lifecycle wait, transport call, success-only caching)
- Compress Section 9 cache behavior details (lines 59-63): replace with prose describing cache policy (success-only, TTL+LRU, key format, side-effect bypass)
- Compress Section 9 health gate state transitions (lines 65-70): replace with prose describing state machine (HEALTHY→DEGRADED→UNAVAILABLE on failures; HALF_OPEN experimental recovery; UNAVAILABLE blocks dispatch)
- Compress Section 9 concurrency behavior (lines 72-75): replace with prose describing concurrency limits (server_key → max concurrent calls mapping via semaphore)
- Compress Section 9 side-effect detection set/listing (lines 78-81): replace with prose describing side-effect tool categories (WRITE_TOOLS, DELETE_TOOLS, shell_run, GIT_WRITE_TOOLS, GITHUB_WRITE_TOOLS, GITHUB_DANGEROUS_TOOLS)
- Keep: RuntimeToolRegistry as sole routing authority, ToolRegistry as drift-validation seed only, HALF_OPEN experimental recovery concept, side-effect tool caution, routing delegation to Agent design docs

### Part 2 (LLMClient + McpServerConfig sections):
- Compress Section 10 LLMClient full constructor signature (lines 29-43): replace with prose describing client responsibilities (HTTP client, retry logic, SSE streaming, error handling, hot config reload)
- Compress Section 10 error behavior exhaustive enumeration (lines 52-57): replace with prose describing error classification categories (HTTP_STATUS_RETRYABLE/FATAL, CONNECT_ERROR, READ_TIMEOUT, HEARTBEAT_TIMEOUT, MALFORMED_SSE_FRAME, UTF8_PARTIAL_DECODE_ERROR, PREMATURE_EOF, UNKNOWN_STREAM_ERROR)
- Compress Section 10 statistics attribute list (line 61): replace with prose describing stats tracked (retries, reconnects, heartbeat timeouts, parse errors)
- Compress Section 10 apply_config target field list (line 65): replace with prose describing hot-reloadable fields (temperature, max_tokens, max_retries, retry_base_delay, sse_heartbeat_timeout, sse_malformed_retry, sse_reconnect_max, stream retry flags)
- Compress Section 11 McpServerConfig field descriptions: replace with prose describing configuration categories (transport, url, cmd, startup_mode, tool_names, auth_token, env)
- Compress Section 11 TransportType/StartupMode/SecurityProfile enum value tables: replace with prose describing enum purposes
- Compress Section 12 execution flow pseudo-code (lines 90-102): replace with prose describing config loading and tool execution flows at conceptual level
- Keep: LLMClient HTTP/retry/SSE/error classification responsibilities, detailed SSE design delegated to Agent docs, LLMTransportError operational meaning, retryable vs fatal judgment criteria, partial_text error handling is agent responsibility, McpServerConfig as shared contract, HealthRegistry MCP transport availability support, load_all() reads only agent.toml config boundary

## Alternatives considered
- Remove Section 9 entirely: rejected — ToolExecutor is central to tool execution architecture
- Replace all tables with prose: rejected — tabular format for type overview is efficient for reference
- Merge Sections 10 and 11 into one: rejected — different conceptual domains (LLM client vs MCP server config)

## Implementation
### Target files
- `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md`
- `docs/90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which LLM/MCP client design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress or remove Section 9 ToolCallResult full dataclass listing (lines 29-37)
   - Part 1: Compress or remove Section 9 execute() sequential steps (lines 42-55)
   - Part 1: Compress or remove Section 9 cache behavior details (lines 59-63)
   - Part 1: Compress or remove Section 9 health gate state transitions (lines 65-70)
   - Part 1: Compress or remove Section 9 concurrency behavior (lines 72-75)
   - Part 1: Compress or remove Section 9 side-effect detection set/listing (lines 78-81)
   - Part 2: Compress or remove Section 10 LLMClient full constructor signature (lines 29-43)
   - Part 2: Compress or remove Section 10 error behavior exhaustive enumeration (lines 52-57)
   - Part 2: Compress or remove Section 10 statistics attribute list (line 61)
   - Part 2: Compress or remove Section 10 apply_config target field list (line 65)
   - Part 2: Compress or remove Section 11 McpServerConfig field descriptions
   - Part 2: Compress or remove Section 11 TransportType/StartupMode/SecurityProfile enum value tables
   - Part 2: Compress or remove Section 12 execution flow pseudo-code (lines 90-102)
   - Preserve: LLMClient HTTP/retry/SSE/error classification, SSE design delegation, LLMTransportError operational meaning, retryable vs fatal criteria, partial_text = agent responsibility, McpServerConfig shared contract, HealthRegistry MCP transport availability, load_all() = agent.toml only

3. **Phase 3: Deployment & Verification**
   - Confirm retryable/fatal judgment criteria not weakened
   - Confirm partial_text handling responsibility clearly stated as agent's
   - Confirm cross-references to `scripts/shared/llm_client.py`, `scripts/shared/mcp_config.py`, `scripts/shared/mcp_health.py` exist
   - Confirm detailed SSE design points to Agent design docs
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (ToolExecutor):
- Section 9 (ToolCallResult): replace dataclass listing with prose: "Frozen dataclass with output (truncated if > MCP_MAX_RESPONSE_BYTES), is_error, request_id (X-Request-Id from MCP server, empty for cache hits), server_key (routing target), source ('mcp'/'cache'/empty), error_type ('transport'/'tool'/empty). error_type used by health gate and error counter aggregation."
- Section 9 (execute flow): replace pseudo-code with prose: "TTL+LRU cache check (success results only); stampede protection shares Future for same-key concurrent calls; resolve tool_name → server_key via ToolRouteResolver; startup_mode=none gate rejects disabled servers; McpServerHealthRegistry.is_unavailable() blocks UNAVAILABLE dispatch (HALF_OPEN allows one attempt per cooldown); lifecycle.ensure_ready() if configured; execute via HttpTransport.call() behind per-server-key semaphore; cache success results only; return ToolCallResult."
- Section 9 (cache): replace bullet list with prose: "Success results only (is_error=False excluded); TTL+LRU eviction configurable via tool_cache_ttl_sec/tool_cache_maxsize; key = (tool_name, serialized_args); side-effect tools fully bypass cache."
- Section 9 (health gate): replace description with prose: "McpServerHealthRegistry.is_unavailable() blocks dispatch when UNAVAILABLE; consecutive transport failures transition HEALTHY→DEGRADED→UNAVAILABLE (failure_threshold reaches UNAVAILABLE); success response resets to HEALTHY (clears failure count/degraded reason). HALF_OPEN exists as experimental circuit-breaker recovery: after half_open_cooldown_sec in UNAVAILABLE, one dispatch attempt allowed; failure during HALF_OPEN returns immediately to UNAVAILABLE; record_degraded() does not override UNAVAILABLE/HALF_OPEN states."
- Section 9 (concurrency): replace with prose: "concurrency_limits maps server_key → max concurrent calls; semaphore-based throttling in ToolTransportInvoker; execute_all_tool_calls() serializes entire round when any side-effect tool detected regardless of serial_tool_calls setting."
- Section 9 (side-effect): replace set/listing with prose: "_SIDE_EFFECT_TOOLS = WRITE_TOOLS | DELETE_TOOLS | {'shell_run'} | GIT_WRITE_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS; is_side_effect(tool_name) checks membership; defined in tool_executor_helpers.py not tool_executor.py; execute_all_tool_calls() in agent/tool_runner.py uses this to switch parallel/serial per-round."
- Section 9 (routing): preserve as-is — already concise and design-critical

#### Part 2 (LLMClient + McpServerConfig):
- Section 10 (constructor): replace with prose: "LLMClient wraps AsyncClient with retry logic, SSE streaming, error handling. Constructor accepts http client, max_retries, retry_base_delay, temperature, max_tokens, optional callbacks (on_token/on_usage), SSE parameters (sse_heartbeat_timeout=30, sse_malformed_retry=2, sse_reconnect_max=1, llm_stream_retry_on_heartbeat_timeout=True, llm_stream_retry_on_malformed_chunk=False). call()/stream() accept url/history/tool_defs; build_payload constructs request dict."
- Section 10 (error behavior): replace exhaustive enumeration with prose: "HTTP errors → LLMTransportError classified by kind: HTTP_STATUS_RETRYABLE (429/503), HTTP_STATUS_FATAL (others), CONNECT_ERROR, READ_TIMEOUT, HEARTBEAT_TIMEOUT, MALFORMED_SSE_FRAME, UTF8_PARTIAL_DECODE_ERROR, PREMATURE_EOF, UNKNOWN_STREAM_ERROR. SSE heartbeat timeout retries if enabled; malformed chunk retries up to sse_malformed_retry times then raises MALFORMED_SSE_FRAME. Retry exhaustion raises LLMTransportError with partial_text containing accumulated output."
- Section 10 (retry): replace with prose: "Exponential backoff starting from retry_base_delay; limit max_retries for non-streaming; streaming reconnection uses separate counter sse_reconnect_max."
- Section 10 (statistics): replace with prose: "Instance-level stats: stat_retries, stat_reconnects, stat_heartbeat_timeouts, stat_parse_errors. Note: stat_partial_completions does not exist; LlmReconnectHandler.stream() returns partial_completions as tuple element but LLMClient.stream() discards without accumulating."
- Section 10 (apply_config): replace with prose: "LlmHotConfigHandler applies hot reload for: temperature, max_tokens, max_retries, retry_base_delay, sse_heartbeat_timeout, sse_malformed_retry, sse_reconnect_max, stream_retry_on_heartbeat_timeout, stream_retry_on_malformed_chunk. None values leave existing values unchanged."
- Section 10 (detail note): preserve — already concise and design-critical
- Section 11 (McpServerConfig): replace with prose: "Per-server transport config (transport, url, cmd, startup_mode, tool_names, auth_token, env) validated by __post_init__ (URL scheme, timeout range, tool_names uniqueness, env type). key field set from TOML section name, excluded from == comparison. TransportType enum replaces plain str. Related enums: StartupMode (none/persistent/subprocess), SecurityProfile (local/production controls MCP auth enforcement). HealthcheckMode enum deleted 2026-07-17 — HTTP was only transport."
- Section 11 (build_discovery_map): preserve — already concise and design-critical
- Section 12 (execution flow): replace pseudo-code with prose: "Config loading: build_agent_config() → ConfigLoader().load_all() reads _BASE_CONFIG_FILES = ('agent.toml',) only. Other configs loaded separately per process isolation policy. Tool execution: ToolExecutor.execute(tool_name, args) → health gate → cache → raw MCP call."
- Remove Related Documents and Keywords sections from both parts — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/shared/tool_executor.py`, `scripts/shared/tool_executor_helpers.py`, `scripts/shared/llm_client.py`, `scripts/shared/llm_exceptions.py`, `scripts/shared/llm_transport_errors.py`, `scripts/shared/sse_parser.py`, `scripts/shared/llm_retry.py`, `scripts/shared/llm_reconnect.py`, `scripts/shared/llm_hot_config.py`, `scripts/shared/mcp_config.py`, `scripts/shared/mcp_health.py`, `scripts/shared/route_resolver.py`, `scripts/shared/runtime_tool_registry.py`, `scripts/shared/tool_registry.py`, `scripts/shared/tool_routing_validation.py` must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` and `docs/04_mcp_*` / `docs/05_agent_*` directories
- No change to source code contracts — document-only modification

## Security considerations
- N/A — document-only modification, no security-sensitive content affected

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files for verification

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Retryable/Fatal Judgment Criteria | Manual | Explicitly preserved |
| Partial Text Handling Responsibility | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/shared/llm_client.py / scripts/shared/mcp_config.py / scripts/shared/mcp_health.py |
| Internal Links | Manual | All cross-references valid |
| Template Compliance | Manual | Follows `memo-doc-shared-review.md` §「修正後の章構成テンプレート」 |

## Out of scope
- Source code changes
- Test modifications
- Cross-chapter structural changes beyond these two files
- Auto-generation of documentation (future work)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260807-211159_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-094430
- Related target files: 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part1.md, 90_shared_03_03_runtime_and_execution-llm-and-mcp-clients-part2.md
