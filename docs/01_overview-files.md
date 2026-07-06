# File Structure

Architecture overview → [`01_overview-arch.md`](01_overview-arch.md)

## 3. File Structure

Deploy destination directory structure:

```
/opt/llm/
├─ llama.cpp/                                 # llama.cpp source & build artifacts
├─ models/
│   ├─ Qwen3.6-Instruct-Q4_K_M.gguf           # LLM (MQE and rerank, :8001)
│   └─ multilingual-E5-small.gguf             # Embedding LLM (384 dim, :8003)
├─ rag-src/                           # Crawled text (yyyymmddhhmmss-{slug}.json)
│   ├─ chunk/                         # Chunked files ({stem}-{idx:04d}.json)
│   └─ registered/                    # DB-inserted files (moved by ingester.py)
├─ db/
│   ├─ rag.sqlite                     # RAG vector DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 §3-§6
│   ├─ session.sqlite                 # Agent session + messages — see 90_shared_04 §2
│   └─ workflow.sqlite                # Task tracking + event processing — see 90_shared_04 §7
├─ sqlite-vec/
│   └─ vec0.so                        # SQLite vector search extension (loadable module)
├─ venv/                              # Python virtual environment
│   └─ requirements.txt              # Python dependency packages
├─ config/
│   ├─ common.toml                          # Common settings (DB paths, embedding URL)
│   ├─ rag_pipeline.toml                    # Crawl & chunk settings (target URLs, chunk size, stopwords)
│   ├─ web_search_mcp_server.toml           # Web search MCP server settings (:8004)
│   ├─ file_read_mcp_server.toml            # File read MCP server settings (:8005, allowed directories)
│   ├─ github_mcp_server.toml               # GitHub MCP server settings (:8006)
│   ├─ file_write_mcp_server.toml           # File write MCP server settings (:8007)
│   ├─ file_delete_mcp_server.toml          # File delete MCP server settings (:8008)
│   ├─ shell_mcp_server.toml                # Shell MCP server settings (:8009, allowed commands)
│   ├─ rag_pipeline_mcp_server.toml         # RAG pipeline MCP server settings (:8010)
│   ├─ cicd_mcp_server.toml                 # CI/CD MCP server settings (:8012)
│   ├─ mdq_mcp_server.toml                  # MDQ MCP server settings (:8013)
│   └─ git_mcp_server.toml                  # Git MCP server settings (:8014)
├─ scripts/
│   ├─ agent.py                             # CLI entry point (launches AgentREPL)
│   ├─ agent/                               # Agent REPL package
│   │   ├─ __main__.py                      # python -m agent entry point
│   │   ├─ repl.py                          # AgentREPL: inject all components into AgentContext, drive REPL loop
│   │   ├─ startup.py                       # StartupOrchestrator: startup sequence
│   │   ├─ config.py                        # AgentConfig dataclass & config loader (hot-reload support)
│   │   ├─ config_builders.py               # Config builders
│   │   ├─ config_dataclasses.py            # Config dataclasses
│   │   ├─ context.py                       # AgentContext: per-session mutable state / DI hub
│   │   ├─ session.py                       # AgentSession: session CRUD (SQLite persistence)
│   │   ├─ session_message_repo.py          # Session message repository
│   │   ├─ history.py                       # Conversation history buffer & compression hook
│   │   ├─ history_selection_policy.py      # History compression selection policy
│   │   ├─ orchestrator.py                  # Orchestrator: turn-level control (RAG → compress → LLM → tool)
│   │   ├─ llm_turn_runner.py               # LLMTurnRunner: SSE streaming + tool loop
│   │   ├─ tool_loop_guard.py               # ToolLoopGuard: dedup/cycle/retry/error guard
│   │   ├─ tool_runner.py                   # Tool execution
│   │   ├─ tool_scheduler.py                # Tool scheduler (parallel/serial)
│   │   ├─ tool_policy.py                   # Tool policy
│   │   ├─ tool_approval.py                 # Tool approval
│   │   ├─ tool_audit.py                    # Tool audit
│   │   ├─ tool_enums.py                    # Tool enums
│   │   ├─ tool_exceptions.py               # Tool exception definitions
│   │   ├─ tool_models.py                   # Tool data models
│   │   ├─ tool_output.py                   # Tool output formatting
│   │   ├─ tool_result_formatter.py         # Tool result formatter
│   │   ├─ repository_gateway.py            # RepositoryGateway: single enforcement boundary for write/delete/API-write (policy → approval → exec → audit)
│   │   ├─ turn_result.py                   # Turn result dataclass
│   │   ├─ diagnostic_store.py              # Partial completion diagnostic info storage
│   │   ├─ error_injection_service.py       # Error injection service
│   │   ├─ mdq_rag_classifier.py            # MDQ RAG classification engine
│   │   ├─ lifecycle_protocol.py            # Lifecycle protocol
│   │   ├─ lifecycle.py                     # LifecycleState enum
│   │   ├─ http_lifecycle.py                # HTTP lifecycle management
│   │   ├─ workflow_execution_policy.py     # WorkflowExecutionPolicy: aggregation of workflow mode determination
│   │   ├─ repl_health.py                   # Health check satellite
│   │   ├─ cli_view.py                      # CLIView: readline config, RAG progress display, multi-line input
│   │   ├─ factory.py                       # AgentFactory: agent component construction
│   │   ├─ memory/
│   │   │   ├─ types.py                     # MemoryEntry / MemoryQuery / MemoryHit / EmbeddingResult dataclasses
│   │   │   ├─ services.py                  # MemoryServices: memory sub-service container (AppServices.memory type)
│   │   │   ├─ store.py                     # MemoryStore: SQLite CRUD (`memories` / `memories_fts` / `memories_vec`)
│   │   │   ├─ retriever.py                 # FtsRetriever / VectorRetriever / HybridRetriever: FTS5 + KNN RRF search
│   │   │   ├─ extract.py                   # extract_memories(): rule-based history extraction
│   │   │   ├─ jsonl_store.py               # JsonlMemoryStore: append-only JSONL source (single write())
│   │   │   ├─ embedding_client.py          # Embedding client
│   │   │   ├─ ingestion.py                 # Memory ingestion
│   │   │   ├─ injection.py                 # Memory injection
│   │   │   ├─ mapper.py                    # Memory mapper
│   │   │   ├─ enums.py                     # Memory enums
│   │   │   ├─ exceptions.py                # Memory exception definitions
│   │   │   ├─ models.py                    # HistoryMessage / JsonlRecord / ConsistencyReport / MemorySnippet dataclasses
│   │   │   ├─ count_ops.py                 # Row count for memories table (by type/source_type)
│   │   │   ├─ write_ops.py                 # Memory write operations
│   │   │   ├─ pin_ops.py                   # Memory pin operations
│   │   │   ├─ import_ops.py                # Memory import operations
│   │   │   ├─ rebuild_ops.py               # Memory rebuild operations
│   │   │   ├─ fts_query.py                 # FTS query helper
│   │   │   ├─ scoring.py                   # Memory scoring
│   │   │   ├─ rrf.py                       # RRF (Reciprocal Rank Fusion) merge
│   │   │   └─ sql_constants.py             # SQL constants
│   │   ├─ commands/
│   │   │   ├─ registry.py                  # CommandRegistry: slash command dispatcher (13 mixins)
│   │   │   ├─ command_defs.py              # CommandDef / SubcommandSpec dataclasses (dataclass definitions only; does not hold _COMMANDS)
│   │   │   ├─ command_defs_list.py         # _COMMANDS: single source for all built-in slash commands (add commands here)
│   │   │   ├─ mixin_base.py                # MixinBase: common base class for all mixins
│   │   │   ├─ output_port.py               # OutputPort / CliOutputPort: command output interface
│   │   │   ├─ enums.py                     # Command enums
│   │   │   ├─ exceptions.py                # Command exception definitions
│   │   │   ├─ models.py                    # Command data models
│   │   │   ├─ utils.py                     # Command utilities
│   │   │   ├─ cmd_session.py               # /session command (_SessionMixin)
│   │   │   ├─ cmd_mcp.py                   # /mcp command (_McpMixin)
│   │   │   ├─ cmd_config.py                # /config, /reload commands (_ConfigMixin)
│   │   │   ├─ cmd_config_display.py        # /config display (_ConfigMixin)
│   │   │   ├─ cmd_config_set.py            # /set command (_ConfigMixin)
│   │   │   ├─ cmd_config_stats.py          # /stats command (_ConfigMixin)
│   │   │   ├─ cmd_context.py               # /context, /clear, /undo, /history, /system commands (_ContextMixin)
│   │   │   ├─ cmd_db.py                    # /db command (_DbMixin)
│   │   │   ├─ cmd_tooling.py               # /tool, /plan commands (_ToolingMixin)
│   │   │   ├─ cmd_debug.py                 # /debug command (_DebugMixin)
│   │   │   ├─ cmd_audit.py                 # /audit command (_AuditMixin)
│   │   │   ├─ cmd_rag_export.py            # /rag, /export, /compact commands (_RagExportMixin)
│   │   │   ├─ cmd_memory.py                # /memory command (_MemoryMixin)
│   │   │   ├─ cmd_mdq.py                   # /mdq command (_MdqMixin): status/index/refresh/search/outline/get/grep
│   │   │   ├─ cmd_plugins.py               # /plugin command (_PluginsMixin): plugin load status display
│   │   │   ├─ cmd_workflow.py              # /approve, /reject commands (_WorkflowMixin)
│   │   │   ├─ db_help_display.py           # DB help display
│   │   │   ├─ db_session_ops.py            # Session DB operations
│   │   │   ├─ db_stats_display.py          # DB status display
│   │   │   ├─ db_rag_ops.py                # RAG DB operation handlers (clean, list_urls, rebuild_fts, vec_rebuild, reconcile_url, recover, consistency)
│   │   │   ├─ memory_data_ops.py           # Memory data operations (list, search, show, pin, delete, prune)
│   │   │   ├─ memory_rebuild_ops.py        # Memory rebuild operations (rebuild, rebuild-fts, rebuild-vec, check-consistency)
│   │   │   ├─ memory_status.py             # Memory layer status display logic (MemoryStatus dataclass)
│   │   │   ├─ session_title.py             # Session title generation logic (LLM-based with fallback)
│   │   │   └─ token_display.py             # Token count display logic (TokenDisplay mixin)
│   │   ├─ services/                        # Service layer (agent/services/ directory)
│   │   │   ├─ enums.py                     # McpTier / McpAvailability / ConversationActionType / ExportFormat
│   │   │   ├─ exceptions.py                # McpProbeError / SessionTitleGenerationError / ConfigReloadValidationError etc.
│   │   │   ├─ models.py                    # SessionTitleResult / McpProbeResult / SessionRestoreResult / DbStats etc.
│   │   │   ├─ config_reload.py             # Config reload
│   │   │   ├─ context_view.py              # Context view
│   │   │   ├─ conversation_service.py      # Conversation service
│   │   │   ├─ db_maintenance_service.py    # DB maintenance service
│   │   │   ├─ export_formatter.py          # Export formatting
│   │   │   ├─ io_ports.py                  # I/O port management
│   │   │   ├─ mcp_status.py                # MCP server status
│   │   │   ├─ rag_maintenance_service.py   # RAG maintenance service
│   │   │   ├─ session_restore.py           # Session restore
│   │   │   ├─ session_title.py             # Session title generation
│   │   │   ├─ typed_validators.py          # Type boundary extraction helper for config reload
│   │   │   └─ undo_service.py              # Undo service
│   │   ├─ shared/                          # Shared types within agent package (agent layer only)
│   │   │    ├─ enums.py                    # Empty file: canonical enums are in agent.memory.enums / agent.tool_enums
│   │   │    ├─ exceptions.py               # Empty file: canonical exceptions are in agent.commands/agent.services/agent.memory/agent.tool_exceptions
│   │   │    ├─ health_models.py            # Health check model
│   │   │    │    ├─ ServiceWarning: label, url, message
│   │   │    │    ├─ HealthCheckResult: warnings, errors; has_issues (prop), warning_messages(), error_messages()
│   │   │    │    └─ McpHealthProbeResult: reachable, status_code, restart_recommended, operator_action_required, body
│   │   │    └─ models.py                   # Agent common data model
│   │   │       ├─ ToolApprovalEvent: event, task_id, tool, operation_type, resource_scope, risk, decision, args_preview, ts, workflow_id, session_id
│   │   │       ├─ ApprovalDecisionEvent: event, task_id, tool, risk_level, decision, escalation_reason, ts, workflow_id, session_id
│   │   │       └─ ToolExecEvent: event, task_id, tool, operation_type, resource_scope, mcp_request_id, is_error, args_preview, ts, source, error_type, workflow_id, session_id, artifact_uri
│   │   └─ workflow/                        # Workflow engine
│   │       ├─ models.py                    # Workflow data models
│   │       ├─ state_store.py               # Workflow state store
│   │       ├─ workflow_engine.py           # WorkflowEngine: turn execution engine
│   │       ├─ workflow_loader.py           # Workflow loader
│   │       ├─ approval_ops.py              # Approval operations (request, resolve, get_pending)
│   │       ├─ artifact_ops.py              # Artifact operations (record_artifact)
│   │       ├─ attempt_ops.py               # Attempt operations (start, finish, count)
│   │       ├─ idempotency_ops.py           # Idempotency operations (is_event_processed, begin_stage_if_new)
│   │       └─ task_ops.py                  # Task CRUD (create, update_status, get_by_id, list_pending)
│   ├─ mcp/                                 # MCP server package
│   │   ├─ models.py                        # /v1/call_tool integration endpoint common Pydantic models
│   │   ├─ server.py                        # MCP server HTTP startup common base class
│   │   ├─ audit.py                         # MCP tool execution audit log (JSON-lines 1 line/execution)
│   │   ├─ dispatch.py                      # dispatch_tool(): tool routing helper returning DispatchResult
│   │   ├─ tool_validators.py               # @register_validator: input validators for git_commit / git_push / trigger_workflow / shell_run etc.
│   │   ├─ web_search/server.py             # Web search MCP server (DuckDuckGo, :8004)
│   │   ├─ file/                            # File MCP servers (:8005/:8007/:8008)
│   │   ├─ github/                          # GitHub MCP server (:8006)
│   │   ├─ shell/                           # Shell MCP server (:8009)
│   │   ├─ rag_pipeline/                    # RAG pipeline MCP server (:8010)
│   │   ├─ cicd/                            # GitHub Actions CI/CD MCP server (:8012)
│   │   ├─ mdq/                             # Markdown Context Compression Engine MCP server (:8013)
│   │   └─ git/                             # Local git operations MCP server (:8014)
│   ├─ rag/                                 # RAG pipeline package
│   │   ├─ pipeline.py                      # RagPipeline: MQE → vector/FTS5 → RRF → rerank
│   │   ├─ pipeline_refiner.py              # refine_context(): reranked hits → key point compression by LLM
│   │   ├─ pipeline_service.py              # call_rag_service(): RAG service HTTP call (exponential backoff retry)
│   │   ├─ http_augment.py                  # HTTP RAG delegation to agent external service
│   │   ├─ repository.py                    # chunks_vec / chunks_fts access layer
│   │   ├─ cache.py                         # SemanticCache: embedding-based LRU semantic cache
│   │   ├─ stage.py                         # PipelineStage Protocol / PipelineContext dataclass
│   │   ├─ maintenance.py                   # RagDbMaintenanceService: FTS5 rebuild, WAL checkpoint, VACUUM
│   │   ├─ llm_client.py                    # RagLLM: RAG-dedicated LLM client (MQE, rerank)
│   │   ├─ llm_prompts.py                   # RAG pipeline LLM prompt templates
│   │   ├─ enums.py                         # RAG enums
│   │   ├─ exceptions.py                    # RAG exception definitions
│   │   ├─ types.py                         # Type definitions for RawHit / MergedHit / RankedHit etc.
│   │   ├─ utils.py                         # RAG utilities
│   │   ├─ models_audit.py                  # RAG audit data model
│   │   ├─ models_config.py                 # RAG config data model
│   │   ├─ models_data.py                   # RAG data model
│   │   ├─ models_result.py                 # RAG result data model
│   │   ├─ ingestion/                       # Crawl, chunk split, DB insertion
│   │   │   ├─ document_manager.py          # Document lifecycle management (RagIngester)
│   │   │   ├─ crawler.py                   # Crawler
│   │   │   ├─ crawler_utils.py             # Crawler utilities
│   │   │   ├─ etag_manager.py              # ETag cache management (crawl delta detection)
│   │   │   ├─ chunk_splitter.py            # Chunk split entry point
│   │   │   ├─ chunk_japanese.py            # Japanese chunk splitting
│   │   │   ├─ chunk_english.py             # English chunk splitting
│   │   │   ├─ chunk_utils.py               # Chunk split utilities
│   │   │   ├─ pipeline_utils.py            # Pipeline utilities
│   │   │   └─ ingester.py                  # DB insertion (move to registered/)
│   │   └─ stages/                          # search / fusion / mqe / augment / rerank
│   ├─ db/                                  # DB layer package
│   │   ├─ __init__.py                      # Module initialization
│   │   ├─ create_schema.py                 # SQLite schema initialization
│   │   ├─ schema_sql.py                    # build_rag_schema_sql / build_session_schema_sql / build_workflow_schema_sql
│   │   ├─ helper.py                        # Connection management (WAL / busy_timeout)
│   │   ├─ maintenance.py                   # Operations policy
│   │   ├─ config.py                        # DbConfig dataclass / SQLite path builder
│   │   ├─ models.py                        # WalCheckpointCounts / PurgeCounts / ToolResultRow / DbHealthMetrics / DocumentRow / SessionRow / MessageRow
│   │   ├─ store.py                         # Protocol abstraction layer
│   │   ├─ store_protocols.py               # VectorStore / DocumentStore / SessionStore Protocol definitions
│   │   ├─ store_impl.py                    # SQLiteVectorStore / SQLiteDocumentStore / SQLiteSessionStore implementations
│   │   ├─ tool_results.py                  # Tool result persistence
│   │   ├─ rag_consistency.py               # RAG index consistency check
│   │   ├─ rotation.py                      # Database rotation
│   │   └─ recovery.py                      # Corrupted DB recovery
│   └─ shared/                              # Shared utility package (accessible from all layers)
│       ├─ llm_client.py                    # LLMClient: SSE streaming, exponential backoff retry
│       ├─ llm_types.py                     # LLMUsage / LLMResponse dataclasses (separated from llm_client for import lightening)
│       ├─ llm_exceptions.py                # LLMErrorKind literal, LLMTransportError error type (kind/phase/url/status_code/retryable/partial_text/detail)
│       ├─ llm_transport_errors.py          # LlmTransportErrorHandler: raise_http_status_error / translate_stream_error
│       ├─ llm_sse_stream.py                # LlmSseStreamHandler: read_next_chunk / stream_once
│       ├─ llm_sse_helpers.py               # LlmSseHelpers: merge_tool_call_delta / build_stream_response
│       ├─ llm_reconnect.py                 # LlmReconnectHandler: resolve_retryable / stream
│       ├─ llm_hot_config.py                # LlmHotConfigHandler: hot reload config fields
│       ├─ llm_retry.py                     # LlmRetryHandler: exponential backoff LLM HTTP request retry
│       ├─ llm_payload.py                   # LlmPayloadHandler: build_payload / parse_response
│       ├─ sse_parser.py                    # RobustSSEParser: stateful SSE parser (UTF-8 incremental decode + heartbeat tracking + bad frame budget)
│       ├─ tool_executor.py                 # ToolExecutor: MCP server routing, TTL cache
│       ├─ tool_executor_helpers.py         # is_side_effect() / format_transport_error() / tool_hash_key(): tool execution helper functions
│       ├─ tool_transport_invoker.py        # ToolTransportInvoker: transport layer MCP calls (health/lifecycle/semaphore/call recording)
│       ├─ tool_registry.py                 # ToolDefinition dataclass, ToolRegistry class — MCP tool registry and drift verification
│       ├─ tool_spec.py                     # ToolSpec: tool call execution metadata (call_id / name / args / resource_scope / requires_serial / is_write)
│       ├─ tool_cache.py                    # CacheEntry dataclass, ToolResultCache — LRU cache + TTL
│       ├─ tool_lifecycle.py                # LifecycleProtocol: MCP server lifecycle protocol
│       ├─ tool_routing_validation.py       # validate_routing_against_config() / validate_routing_against_live() / validate_all_routing(): drift validation functions
│       ├─ tool_constants.py                # Tool classification frozenset (READ/WRITE/DELETE/RAG/CICD/MDQ/GIT)
│       ├─ types.py                         # Common type definitions (LLMMessage, RagConfig, RagHit/RawHit/MergedHit/RankedHit, LLMUsage, LLMResponse, ActionResult, ArtifactEvent, ShellPolicy, tool frozenset)
│       ├─ mcp_config.py                    # McpServerConfig dataclass, re-exports McpServerHealthState / McpServerHealthRegistry
│       ├─ mcp_health.py                    # McpServerHealthState (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN) enum, McpServerHealthRegistry — dispatch gate health tracking
│       ├─ config_loader.py                 # TOML/JSON common config loader
│       ├─ config_errors.py                 # ConfigMissingError / ConfigParseError / ConfigReadError / ConfigPermissionError error types
│       ├─ config_validator.py              # RagConfigValidator: embedding_dim/vec_dim consistency check, use_rrf warning, semantic_cache_threshold health check
│       ├─ plugin_registry.py               # Plugin registration decorator (@register_command etc.)
│       ├─ plugin_registries.py             # Plugin registry list
│       ├─ plugin_tool_invoker.py           # PluginToolInvoker: plugin tool invocation (defensive tuple validation)
│       ├─ plugin_auto_discover.py          # load_plugins(): auto-discovery of plugins from *.py + conflict validation
│       ├─ plugin_conflicts.py              # Plugin conflict detection
│       ├─ plugin_result.py                 # PluginFailure / PluginLoadResult dataclasses, PluginLoadError exception
│       ├─ route_resolver.py                # ToolRouteResolver: tool name → server key mapping
│       ├─ action_result.py                 # ActionResult dataclass (ActionType literal) — generic action/result schema for machine decision path
│       ├─ events.py                        # ArtifactEvent / RetryEvent TypedDict — lifecycle/artifact notification type definitions (no delivery mechanism)
│       ├─ transport_dto.py                 # ToolCallResult / TransportErrorInfo dataclasses — MCP tool execution result and transport failure info
│       ├─ formatters.py                    # MCP all-server common output formatter (truncate / fmt_size / fmt_md_link / fmt_kvlog etc.)
│       ├─ git_helper.py                    # get_repo_info(): branch/commit info via GitPython (/context display)
│       ├─ json_utils.py                    # orjson wrapper: dumps() returns str not bytes
│       ├─ logger.py                        # Logger: entry point file logger (structured log JSON-lines support)
│       ├─ otel_tracer.py                   # OpenTelemetry tracer configuration
│       ├─ otel_noop.py                     # NoOpTracer / NoOpSpan: OpenTelemetry no-op implementation
│       ├─ token_counter.py                 # Token counter
│       ├─ token_estimation.py              # estimate_tokens_for_text() / estimate_tokens_for_assistant_with_tool_calls(): category-based token estimation
│       ├─ http_transport.py                # TransportError / HttpTransport: HTTP transport layer (/v1/call_tool calls)
│       └─ protocols/                       # Shared protocol definitions (shell.py: ShellPolicy)
  └─ logs/                                    # Log file output destination for each service
/etc/conf.d/
    └─ github-mcp                         # GITHUB_TOKEN (Personal Access Token) configuration
```
