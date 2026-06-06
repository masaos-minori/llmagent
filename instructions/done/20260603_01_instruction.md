# Refactoring Instructions

## `mcp/echo_server.py`

* Do not silently `continue` on invalid input.
* Improve observability for malformed requests.
* At minimum, add one of the following:
  * debug output that can be observed during tests, or
  * counters/metrics for malformed input and ignored requests.
* Ensure failure causes can be diagnosed during integration testing.

***

## `mcp/installer.py`

* Split this module by responsibility.

* Do not keep all string template generation in a single file.

* Separate the following concerns into distinct modules or layers:
  * validation
  * port allocation
  * template rendering
  * file writing
  * role-specific snippet generation

* Refactor these functions in particular so that each handles only one concern:
  * `generate_server_script()`
  * `generate_agent_toml_mcp_snippet()`
  * `tool_definition_snippet()`

* Replace the current `scan_used_ports()` design.

* Do not infer port assignments by parsing `--port` from `init.d` scripts with regex.

* Manage port allocation from configuration data instead of script text.

***

## `mcp/service.py`

* Remove the direct dependency from `_build_service()` to `mcp.git.models._get_cfg`.
* Do not let the service layer depend on a global configuration accessor.
* Inject configuration explicitly from the outside.
* Make service construction deterministic and testable.

***

## `mcp/server.py`

* Expose truncation as structured response metadata.

* Do not encode truncation only as a human-readable string appended to the response body.

* Return machine-readable fields such as:
  * `truncated: bool`
  * `total_bytes: int`

* Split this module by responsibility.

* Do not keep the following in the same module:
  * `dispatch_tool()`
  * `_handle_tool_exception()`
  * `attach_auth_middleware()`
  * `MCPServer`

* Separate these concerns:
  * HTTP transport foundation
  * exception policy
  * audit logging
  * dispatch/routing

* Refactor into modules such as:
  * `transport/http.py`
  * `dispatch.py`
  * `audit.py`

***

## `mcp/models.py`

* Do not keep `args` as an unconstrained `dict[str, Any]` without tool-specific validation.

* Even if this remains the common entry point, introduce one of the following:
  * an additional validation layer based on `name`, or
  * a conversion layer from the generic request to tool-specific request schemas

* Ensure tool-specific argument constraints are modeled explicitly.

***

## `agent/memory/types.py`

* Add invariants to the types themselves.

* Do not rely on `jsonl_store.py` or `store.py` to normalize or patch values ad hoc.

* Ensure fields such as the following are validated at the type layer:
  * `memory_type`
  * `source_type`
  * `importance`
  * `created_at`

* Introduce explicit validation using one of the following:
  * `__post_init__`
  * a dedicated validation layer such as Pydantic

* Revisit `SOURCE_TYPES`.

* Do not keep source taxonomy as a fixed set that is difficult to extend.

* Support future source types such as:
  * user note
  * manual pin
  * imported knowledge

* Introduce either:
  * an enum-based taxonomy, or
  * a versioned schema for source classification

***

## `agent/memory/store.py`

* Remove duplicated row-to-model conversion logic.

* Unify `_row_to_entry()` in `store.py` and `_row_to_entry()` in `retriever.py` into a shared mapper.

* Ensure field additions or removals cannot diverge between storage and retrieval paths.

* Make multi-table synchronization explicit and atomic.

* `MemoryStore` is responsible for syncing:
  * `memories`
  * `memories_fts`
  * `memories_vec`

* Ensure upserts that include FTS and vector updates always run inside a single transaction.

* Add a consistency-check API for detecting mismatches across these tables.

* Validate embedding dimensions at storage time.

* Do not serialize vectors with `_floats_to_blob()` without strict dimension checks.

* `memory_embed_dim` is assumed to exist in configuration.

* Reject invalid vector length on write instead of allowing silent corruption that only appears at retrieval time.

***

## `agent/memory/retriever.py`

* Make the scoring policy configurable.

* Do not hardcode retrieval quality tuning in module-level constants.

* Separate and inject the following as config:
  * importance boost
  * recency boost
  * pin boost
  * context boost

* Replace the current `_build_fts_query()` strategy.

* Do not rely only on:
  ```python
  re.findall(r"\w+", text)
  ```
  plus `OR`-joined MATCH queries.

* Make tokenization configurable.

* Support multilingual input, symbols, code fragments, and Japanese text without explicit word boundaries.

* Refactor `_recency_boost()`.

* Do not use a fixed policy that linearly boosts only entries created within 7 days and assigns 0 otherwise.

* Retrieval lifetime should differ by:
  * memory type
  * pinned vs non-pinned state

* Avoid over-applying episodic-style recency decay to semantic memory.

* Otherwise stable long-term rules may be buried.

* Externalize retrieval policy by memory type.

* Make these values configurable and measurable:
  * `_FTS_CANDIDATE_LIMIT = 50`
  * `_RRF_K = 60`

* Do not keep these as unexplained fixed constants.

* Allow tuning based on metrics and benchmark results as data volume grows.

***

## `agent/memory/extract.py`

* Redesign extraction strategy.

* Do not rely primarily on simple heuristics over assistant messages.

* This risks missing important user-origin knowledge such as:
  * persistent rules
  * explicit constraints
  * approval outcomes

* Because `MemoryLayer` injects relevant memory into the system prompt, extraction must not overfit to assistant-only content.

* Expand extraction scope to include:
  * user messages
  * tool outputs where appropriate
  * command or operational events where appropriate

* Replace the current classification strategy.

* Do not rely only on keyword density and message length thresholds to classify semantic vs episodic memory.

* This is too weak against misclassification.

* For example:
  * code review guidance or operating rules may not contain your semantic keywords
  * generic statements containing “should” or “must” may be incorrectly classified as semantic

* Introduce a two-stage extraction flow:
  1. candidate extraction
  2. stricter classifier-based confirmation

* Refactor `_make_summary()`.

* Do not generate summaries only from the first line or first `max_chars`.

* The summary should be useful not only for display, but also for later review and retrieval.

* Introduce structured summary templates for:
  * rules
  * decisions
  * failure causes
  * fixes or corrective actions

* Make the `MAX_ENTRIES = 20` cap policy explicit.

* The cap is useful for noise suppression, but the prioritization logic must be defined.

* Explicitly specify what wins when the cap is reached, for example:
  * longer entries first
  * higher importance first
  * deduplicated entries first

* Ensure important memory is not dropped at session end due to undefined prioritization.

***

## `agent/memory/jsonl_store.py`

* Treat concurrency as a real risk.

* The docstring already says:
  * “Thread-unsafe — use from a single asyncio event loop”

* However, `MemoryLayer` runs asynchronously through session hooks.

* Do not rely on naive append-only writes if concurrent tasks or multiple processes may write.

* Introduce one or more of the following:
  * file locking
  * atomic append guarantees
  * writer serialization

* Strengthen source-of-truth reliability.

* `read_all()` currently warns and skips malformed lines, but that is not sufficient for a canonical store.

* If JSONL is the source of truth, add at least one of the following:
  * compaction
  * repair
  * checksum validation
  * backup/checkpoint strategy

***

## `agent/memory/layer.py`

* Split `MemoryLayer` by responsibility.

* Do not let a single class own all of the following:
  * external embedding retrieval
  * retrieval orchestration
  * dedup link management
  * session hook contracts

* Refactor into separate services such as:
  * `EmbeddingClient`
  * `MemoryIngestionService`
  * `MemoryInjectionService`
  * `MemoryDedupService`

* Improve embedding failure handling.

* Do not stop at logging a warning and returning `None` on HTTP failure in `_fetch_embedding()`.

* Make the following explicit:
  * retry policy
  * timeout policy
  * circuit breaker behavior
  * degraded-mode fallback when embedding quality or service availability is reduced

* Clarify and formalize system injection policy.

* `on_user_prompt()` injects retrieved memories into history as `system` messages.

* Do not leave the following undefined:
  * number of injected memories
  * injection format
  * duplicate injection prevention
  * pin priority

* Without a clear policy, context pollution becomes likely.

* Define a system injection policy and make it consistent with:
  * history compression
  * deduplication
  * prompt budget limits

* Elevate deduplication policy into an explicit API and type model.

* The current description says that embeddings closer than `dedup_threshold` are linked in `memory_links`, but the actual action policy is unclear.

* Make the behavior explicit:
  * link only
  * upsert
  * merge
  * skip

* Because this directly affects memory accumulation quality, do not leave dedup behavior implicit.

***

## General Refactoring Rules

* Keep changes incremental and behavior-preserving unless the requirement explicitly changes behavior.
* Separate:
  * validation
  * orchestration
  * persistence
  * transport
  * logging/audit
* Prefer:
  * explicit dependency injection
  * typed configuration
  * machine-readable metadata
  * deterministic failure handling
* Avoid:
  * hidden global config access
  * silent failure paths
  * duplicated mapping logic
  * hardcoded ranking policy without tunable configuration

