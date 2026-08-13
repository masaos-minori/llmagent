## Goal
- Restructure `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md` and `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md` to remove overly detailed constructor signatures, method listings, dataclass definitions, and exhaustive state transition tables while explicitly preserving why retry is limited to transient failures, ToolResultCache is not used by ToolExecutor, cache duplication is a known issue, ToolSpec is DAG scheduling metadata, HealthRegistry has circuit-breaker semantics, and hot-reloadable LLM config is explicitly maintained.

## Scope
- **In-Scope**: 
  - `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
  - `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md` — restructure to reduce implementation detail while preserving design-intent-critical facts
- **Out-of-Scope**: Other shared/runtime chapters (`docs/90_shared_*.md`), source code changes, tests

## Assumptions
- `memo-doc-shared-review.md` is valid and these chapters should describe "why caching/retry/health infrastructure decisions exist"
- Cache duplication concern must survive as Known Issues note
- Existing internal links and cross-references must remain valid after editing

## Design decisions
### Part 1 (Caching and Reference):
- Compress Section 14 LlmRetryHandler full method signature (lines 29-36): replace with prose describing retry behavior (exponential backoff, transient failure classification)
- Compress Section 15 ToolResultCache/CacheEntry full dataclass listing (lines 50-62): replace with prose describing cache contract categories (output, is_error, cached_at, key format, store-if-success policy)
- Compress Section 16 ToolSpec full dataclass definition (lines 71-80): replace with prose describing metadata categories (call_id, name, args, resource_scope, requires_serial, is_write)
- Compress Section 20 AI Reference table (lines 109-120): replace with prose descriptions where tabular format adds no reference value beyond what's already described in other sections
- Preserve: retry limited to transient failures, ToolResultCache not used by ToolExecutor, cache duplication as known issue, ToolSpec as DAG scheduling metadata, HealthRegistry circuit-breaker semantics, hot-reloadable LLM config

### Part 2 (Health Registry + Handlers):
- Compress Section 17 McpServerHealthState full enum value table (lines 27-32): replace with prose describing state machine purpose
- Compress Section 17 McpServerHealthRegistry full method list (lines 34-43): replace with prose describing health gate responsibilities
- Compress Section 17 exhaustive state transition table (lines 46-52): replace with prose describing state transitions at conceptual level
- Compress Section 17 `[Explicit in code — 追加]` bullet list (lines 54-58): replace with prose describing guard behaviors
- Compress Section 18 LlmPayloadHandler full method signatures (lines 65-73): replace with prose describing payload building/parsing responsibilities
- Compress Section 18 `[Explicit in code — 訂正]` correction bullets (lines 78-82): replace with prose describing method contracts
- Compress Section 19 LlmHotConfigHandler full field/method listing (lines 89-103): replace with prose describing hot-reload capability
- Remove Related Documents and Keywords sections from both parts — content duplicated in frontmatter

## Alternatives considered
- Remove Section 17 entirely: rejected — HealthRegistry is central to MCP transport availability judgment
- Replace all tables with prose: rejected — tabular format for type overview is efficient for reference
- Merge Sections 18 and 19 into one: rejected — different conceptual domains (payload handling vs hot config)

## Implementation
### Target files
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md`
- `docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md`

### Procedure
1. **Phase 1: Preparation**
   - Analyze current document structure and identify which caching/retry/health design judgments are scattered across sections

2. **Phase 2: Core Logic Implementation**
   - Part 1: Compress or remove Section 14 LlmRetryHandler full method signature (lines 29-36)
   - Part 1: Compress or remove Section 15 ToolResultCache/CacheEntry full dataclass listing (lines 50-62)
   - Part 1: Compress or remove Section 16 ToolSpec full dataclass definition (lines 71-80)
   - Part 1: Compress or remove Section 20 AI Reference table (lines 109-120)
   - Part 2: Compress or remove Section 17 McpServerHealthState full enum value table (lines 27-32)
   - Part 2: Compress or remove Section 17 McpServerHealthRegistry full method list (lines 34-43)
   - Part 2: Compress or remove Section 17 exhaustive state transition table (lines 46-52)
   - Part 2: Compress or remove Section 17 `[Explicit in code — 追加]` bullet list (lines 54-58)
   - Part 2: Compress or remove Section 18 LlmPayloadHandler full method signatures (lines 65-73)
   - Part 2: Compress or remove Section 18 `[Explicit in code — 訂正]` correction bullets (lines 78-82)
   - Part 2: Compress or remove Section 19 LlmHotConfigHandler full field/method listing (lines 89-103)
   - Preserve: retry limited to transient failures, ToolResultCache not used by ToolExecutor, cache duplication as known issue, ToolSpec as DAG scheduling metadata, HealthRegistry circuit-breaker semantics, hot-reloadable LLM config

3. **Phase 3: Deployment & Verification**
   - Confirm cache duplication concern preserved as Known Issues note
   - Confirm cross-references to `scripts/shared/tool_cache.py`, `scripts/shared/llm_retry.py`, `scripts/shared/mcp_health.py`, `scripts/shared/llm_payload.py`, `scripts/shared/llm_hot_config.py` exist
   - Confirm retryable/fatal judgment criteria not weakened
   - Validate internal Markdown links and cross-references
   - Confirm compliance with post-edit chapter structure template from `memo-doc-shared-review.md`

### Method
- Table reduction: convert full-field tables to category-level descriptions
- Code block removal: replace inline Python definitions with prose summaries of field semantics
- Pseudo-code removal: replace procedural pseudo-code with behavioral descriptions
- Prose compression: convert field-by-field enumeration to grouped descriptions by purpose

### Details
#### Part 1 (Caching and Reference):
- Section 14 (LlmRetryHandler): replace method signature with prose: "Exponential backoff retry for HTTP POST requests to LLM endpoints. Retries on 429 (rate limit), 503 (service unavailable), and httpx.RequestError (connection error). Non-transient HTTP errors (4xx/5xx other than 429/503) raised immediately. Delay formula: retry_base_delay * (2**attempt) where attempt starts at 0. Last exception raised when all retries exhausted."
- Section 15 (ToolResultCache/CacheEntry): replace dataclass listing with prose: "Frozen dataclass CacheEntry with output (str), is_error (bool), cached_at (float). Standalone LRU+TTL cache utility for tool results. Not currently used by ToolExecutor; kept for potential future use without stampede protection. Key = {tool_name}:{json_dumps(args)} using shared.json_utils.dumps. store_if_success() stores only is_error=False results."
- Section 16 (ToolSpec): replace dataclass listing with prose: "Frozen dataclass for DAG scheduling metadata. call_id (LLM-assigned tool call id from tool_calls[].id), name (tool function name), args (dict[str, object]), resource_scope (resource path/branch string for conflict detection), requires_serial (forces serialization regardless of parallel mode), is_write (used by is_side_effect() to classify write/delete tools). DAG execution layer builds ToolSpec for each approved tool call."
- Section 20 (AI Reference): replace table with prose: "Config loading via ConfigLoader().load('filename.toml') or load_all(); process ownership per §2a; load_all() reads agent.toml only (_BASE_CONFIG_FILES=('agent.toml',)); ToolExecutor uses OrderedDict-based _execute_with_cache() not standalone ToolResultCache; git_helper.get_repo_info() returns RepoInfoResult with .success/.failure_reason; exact token count via await get_token_count(history, tokenize_url, http); LLM retry uses exponential backoff retry_base_delay*(2**attempt); ToolExecutor cache key = {tool_name}:{json_dumps(args)}; health gate state transitions per §17."

#### Part 2 (Health Registry + Handlers):
- Section 17 (McpServerHealthState): replace enum table with prose: "Enum for MCP server health states: HEALTHY (normal operation), DEGRADED (failing but not yet unavailable), UNAVAILABLE (circuit breaker open), HALF_OPEN (experimental probe after cooldown), UNKNOWN (unregistered key returns HEALTHY default, UNKNOWN never observed in practice)."
- Section 17 (McpServerHealthRegistry): replace method list with prose: "Per-server health tracking for ToolExecutor dispatch gating. Constructor accepts failure_threshold (default 3 consecutive failures → UNAVAILABLE) and half_open_cooldown_sec (default 30s). Methods: record_failure() transitions HEALTHY→DEGRADED→UNAVAILABLE; record_degraded() records watchdog reachability probes (does not override UNAVAILABLE/HALF_OPEN); record_restart_exhausted() tags degraded reason as 'restart_limit_reached'; record_success() resets to HEALTHY plus clears failure counts/degraded reasons; get_state() returns current state; is_unavailable() handles UNAVAILABLE→HALF_OPEN transition on cooldown expiry."
- Section 17 (state transitions): replace table with prose: "HEALTHY→DEGRADED on first failure; DEGRADED→UNAVAILABLE on failure_threshold consecutive failures (default 3); UNAVAILABLE→HALF_OPEN after half_open_cooldown_sec (default 30s, experimental probe); HALF_OPEN→UNAVAILABLE on probe failure (cooldown resets); HALF_OPEN→HEALTHY on probe success; any state→HEALTHY on successful response."
- Section 17 (explicit additions): replace bullet list with prose: "get_state() returns HEALTHY default for unregistered keys (UNKNOWN never observed). record_degraded() does not override UNAVAILABLE/HALF_OPEN states (intentional guard against breaking circuit breaker/trial window). record_restart_exhausted() does not change state (assumes record_failure() already set UNAVAILABLE), only tags degraded reason. record_success() resets _failure_counts/_unavailable_since/_degraded_reasons (prevents immediate re-UNAVAILABLE on next failure due to stale counts)."
- Section 18 (LlmPayloadHandler): replace method signatures with prose: "Static methods for building/parsing LLM request/response payloads. build_payload() constructs dict with messages/tools/tool_choice='auto'/temperature/max_tokens; adds 'stream':True when stream=True. parse_response() parses raw JSON dict (not httpx.Response) into LLMResponse DTO; validates choices/message structure raises ValueError. parse_non_stream_response() decodes bytes via orjson.loads then delegates to parse_response(). All methods @staticmethod."
- Section 18 (corrections): replace bullet list with prose: "build_payload() takes temperature (float) and max_tokens (int) as required args (was missing in old doc). parse_response() first arg is raw: dict[str, Any] (parsed JSON, not httpx.Response). parse_non_stream_response() is third method not in old doc. on_usage is Callable[[int, int], None]|None called from LlmSseHelpers.parse_usage(prompt_tokens, completion_tokens); only production caller is scripts/agent/factory.py._on_llm_usage."
- Section 19 (LlmHotConfigHandler): replace field/method listing with prose: "Manages hot-reloadable config fields for LLMClient. HOT_CONFIG_FIELDS is tuple of (instance_attr_name, kwarg_name) pairs for 9 fields: temperature, max_tokens, max_retries, retry_base_delay, sse_heartbeat_timeout, sse_malformed_retry, sse_reconnect_max, stream_retry_on_heartbeat_timeout, stream_retry_on_malformed_chunk. apply_config() accepts keyword-only args, applies setattr via apply_one() only for non-None values (partial update, unchanged fields left alone)."
- Remove Related Documents and Keywords sections from both parts — content duplicated in frontmatter

## Compatibility considerations
- Cross-references to `scripts/shared/tool_cache.py`, `scripts/shared/llm_retry.py`, `scripts/shared/mcp_health.py`, `scripts/shared/llm_payload.py`, `scripts/shared/llm_hot_config.py`, `scripts/shared/json_utils.py`, `scripts/shared/llm_sse_helpers.py`, `scripts/agent/factory.py` must remain valid after restructuring
- Internal Markdown links must be verified against actual file paths in `docs/90_shared_*` directories
- No change to source code contracts — document-only modification

## Security considerations
- N/A — document-only modification, no security-sensitive content affected

## Rollback considerations
- If restructuring causes link breakage, revert to original structure and apply targeted compression instead of full rewrite
- All removed details point to source files for verification

## Validation plan
| Check | Tool | Target |
|---|---|---|
| Cache Duplication Concern | Manual | Explicitly preserved as Known Issues note |
| Retryable/Fatal Judgment Criteria | Manual | Explicitly preserved |
| Cross-references | Manual | All removed details point to scripts/shared/ cache/retry/health infrastructure modules |
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
- Source plan: plans/20260807-211312_plan.md
- Source implementation procedure: N/A
- Generated at: 20260808-094600
- Related target files: docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part1.md, docs/90_shared_03_04_runtime_and_execution-caching-and-reference-part2.md
