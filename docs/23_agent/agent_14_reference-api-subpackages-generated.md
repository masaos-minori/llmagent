---
title: "Agent Reference API — Generated Subpackage Class/Function Index"
area: agent
class: Reference
tags:
  - agent
  - api-reference
  - generated
related:
  - agent_12_reference-api.md
  - agent_13_reference-api-generated.md
---

# Agent Reference API — Generated Subpackage Class/Function Index

## Purpose

Generated index of every public top-level class/function under the
`scripts/agent/` subpackages (`workflow/`, `services/`, `commands/`, `shared/`)
(`tools/generate_reference_table.py --manifests`). Companion to
[agent_12_reference-api.md](agent_12_reference-api.md) (hand-curated) and
[agent_13_reference-api-generated.md](agent_13_reference-api-generated.md)
(top-level `scripts/agent/*.py` symbols); split into its own file to stay under
the per-document size threshold. `scripts/agent/memory/` symbols are covered by
`agent_11_04_memory-module-reference-generated.md`, not by this index. Do not
hand-edit between the guard comments — run the generator.

## Keywords

- agent
- api-reference
- generated

## Subpackage Class/Function Reference (auto-generated)

<!-- AUTO-GENERATED: generate_reference_table.py agent-subpackages-class-function-reference -->
Generated from `registry/manifests/agent_api.yaml` (`scripts/agent/` subpackage symbols: `workflow/`, `services/`, `commands/`, `shared/`; the top-level symbols live in `docs/23_agent/agent_13_reference-api-generated.md`). Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --manifests` to refresh.

| File | Class/Function | Signature | Summary |
|---|---|---|---|
| `scripts/agent/commands/cmd_memory.py` | `MemoryOpResult` | `class MemoryOpResult` | Structured result of a memory state-changing operation. |
| `scripts/agent/commands/command_defs.py` | `ArgSpec` | `class ArgSpec` | One argument of a command or subcommand. |
|  | `format_usage` | `def format_usage(command, subcommand, args) -> str` | Return the usage line, e.g. "/session list [n]". |
|  | `SubcommandSpec` | `class SubcommandSpec` | Declarative metadata for one subcommand. |
|  | `CommandDef` | `class CommandDef` | Declarative metadata for one slash command. |
| `scripts/agent/commands/db_session_ops.py` | `DbSessionOps` | `class DbSessionOps` | Handles session database operations: health, checkpoint, vacuum, purge, recover. |
| `scripts/agent/commands/enums.py` | `CommandKind` | `class CommandKind` | Categories of slash commands available in the agent REPL. |
|  | `MemoryAction` | `class MemoryAction` | Actions available under the /memory command group. |
|  | `DbAction` | `class DbAction` | Actions available under the /db command group. |
|  | `McpAction` | `class McpAction` | Actions available under the /mcp command group. |
|  | `SessionAction` | `class SessionAction` | Actions available under the /session command group. |
| `scripts/agent/commands/exceptions.py` | `CommandParseError` | `class CommandParseError` | Raised when a command line cannot be parsed into a valid command. |
|  | `CommandValidationError` | `class CommandValidationError` | Raised when parsed command arguments fail domain validation. |
|  | `CommandDispatchError` | `class CommandDispatchError` | Raised when a command cannot be dispatched (e.g. unknown command name). |
|  | `CommandRenderingError` | `class CommandRenderingError` | Raised when rendering a command result fails. |
|  | `UnknownSubcommandError` | `class UnknownSubcommandError` | Raised when a slash-command subcommand name is not recognized. |
|  | `UnknownPresetError` | `class UnknownPresetError` | Raised when a command preset name is not recognized. |
|  | `UnknownTierError` | `class UnknownTierError` | Raised when a tool safety tier name is not recognized. |
| `scripts/agent/commands/memory_data_ops.py` | `MemoryDataOps` | `class MemoryDataOps` | Handles memory data operations: list, search, show, pin, delete, prune. |
| `scripts/agent/commands/memory_rebuild_ops.py` | `RebuildResult` | `class RebuildResult` | Result of a memory rebuild operation. |
|  | `MemoryRebuildOps` | `class MemoryRebuildOps` | Handles memory rebuild/reindex operations (rebuild, reindex, check-consistency). |
| `scripts/agent/commands/memory_status.py` | `MemoryStatus` | `class MemoryStatus` | Structured representation of memory layer status for display. |
|  | `build_status_table` | `def build_status_table(status) -> list[list[str]]` | Build a table of rows for display. |
|  | `build_memory_status` | `def build_memory_status(mem, cfg) -> MemoryStatus \| None` | Build a MemoryStatus from a MemoryServices instance. |
| `scripts/agent/commands/mixin_base.py` | `reset_session_stats` | `def reset_session_stats(ctx) -> None` | Reset all per-session counters to zero. |
|  | `refresh_session_correlation` | `def refresh_session_correlation(ctx) -> None` | Refresh the MCP transport correlation id after a session-id change. |
|  | `MixinBase` | `class MixinBase` | Shared annotation base for CommandRegistry mixins. |
| `scripts/agent/commands/models.py` | `LatencySnapshot` | `class LatencySnapshot` | Per-tool latency stats mapping tool_name to a list of elapsed-second samples. |
|  | `MaskedArgs` | `class MaskedArgs` | Decoded and masked tool arguments for display (arg_name -> masked value). |
|  | `StatsViewModel` | `class StatsViewModel` | Aggregated statistics from an active agent session. |
| `scripts/agent/commands/output_port.py` | `OutputPort` | `class OutputPort` | Interface for writing structured output from slash commands. |
|  | `CliOutputPort` | `class CliOutputPort` | Concrete OutputPort that writes to stdout via print(). |
| `scripts/agent/commands/registry.py` | `CommandRegistry` | `class CommandRegistry` | Slash-command dispatcher for AgentREPL. |
| `scripts/agent/commands/session_title.py` | `SessionTitleGen` | `class SessionTitleGen` | Handles session title generation (LLM-based with fallback). |
| `scripts/agent/commands/token_display.py` | `TokenDisplay` | `class TokenDisplay` | Provides token count display methods. |
| `scripts/agent/commands/utils.py` | `ParsedArgs` | `class ParsedArgs` | Structured result of command argument parsing. |
|  | `parse_command_args` | `def parse_command_args(tokens) -> ParsedArgs` | Parse command tokens into a structured ParsedArgs. |
|  | `parse_int_arg` | `def parse_int_arg(raw, *, usage, default, minimum, maximum) -> int \| None` | Parse a command argument into an int, raising on invalid or out-of-range input. |
| `scripts/agent/services/config_field_registry.py` | `ConfigFieldRegistry` | `class ConfigFieldRegistry` | A single entry in CONFIG_FIELD_REGISTRY. |
|  | `registry_for` | `def registry_for(section_path) -> list[ConfigFieldRegistry]` | Return the hot-reloadable ConfigFieldRegistry entries for the given section path. |
|  | `startup_only_for` | `def startup_only_for(section_path) -> list[ConfigFieldRegistry]` | Return the ConfigFieldRegistry entries the given section reads only at startup. |
|  | `validate_section_fields` | `def validate_section_fields(section_path, section) -> None` | Run every registered validator for one section against a built section. |
| `scripts/agent/services/config_outcome_classification.py` | `PendingChange` | `class PendingChange` | One startup-only configuration change `/reload` records instead of applying live. |
|  | `diff_mcp_definitions` | `def diff_mcp_definitions(live_mcp, candidate_mcp) -> list[PendingMcpRecord]` | Return one record per MCP server the candidate redefines. |
|  | `classify_startup_only_fields` | `def classify_startup_only_fields(ctx, candidate) -> list[PendingChange]` | Return pending records for startup-only fields the candidate changes. |
|  | `detect_diagnostics_live_fields` | `def detect_diagnostics_live_fields(ctx, new_cfg) -> list[str]` | Return names of diagnostics.* fields that differ between new_cfg and running cfg. |
| `scripts/agent/services/config_pending_state.py` | `PendingMcpRecord` | `class PendingMcpRecord` | One MCP server definition change `/reload` recorded instead of applying. |
|  | `PendingConfigState` | `class PendingConfigState` | Restart-pending configuration records and the degraded-reload guard. |
|  | `pending_state_for` | `def pending_state_for(ctx) -> PendingConfigState \| None` | Return the pending state the context's container carries, or None. |
| `scripts/agent/services/config_reload.py` | `ConfigReloadOutcome` | `class ConfigReloadOutcome` | Structured report of what changed after a /reload. |
|  | `ConfigReloadService` | `class ConfigReloadService` | Propagate an updated config dict to live service instances. |
| `scripts/agent/services/config_reload_transaction.py` | `ReloadStage` | `class ReloadStage` | Stage a `/reload` ended in. |
|  | `CommitPhase` | `class CommitPhase` | Fixed commit order. Steps run in this order, not in registration order. |
|  | `PreparedStep` | `class PreparedStep` | One reversible change prepared before commit. |
|  | `ReloadTransaction` | `class ReloadTransaction` | Snapshot, commit, and rollback owner for one `/reload`. |
| `scripts/agent/services/config_section_reload.py` | `SectionCandidate` | `class SectionCandidate` | A prepared, validated candidate for one configuration section. |
|  | `prepare_validated_section` | `def prepare_validated_section(ctx, section_path, candidate_section, extra_changed_fields) -> SectionCandidate \| None` | Diff one hot-reloadable section of the typed candidate against the live section and run its validators. |
|  | `apply_validated_section` | `def apply_validated_section(ctx, candidate) -> UndoToken` | Commit a prepared validated-section candidate onto ctx.cfg. |
| `scripts/agent/services/config_service_sync.py` | `ServiceSyncer` | `class ServiceSyncer` | Propagates config changes to live service instances. |
| `scripts/agent/services/config_validators.py` | `validate_llm_context_char_limit` | `def validate_llm_context_char_limit(cfg) -> None` | Validate that context_char_limit is a non-negative int. |
|  | `validate_llm_budget_warn_ratio` | `def validate_llm_budget_warn_ratio(cfg) -> None` | Validate that budget_warn_ratio is in (0.0, 1.0]. |
|  | `validate_llm_retry_base_delay` | `def validate_llm_retry_base_delay(cfg) -> None` | Validate that llm_retry_base_delay is positive. |
|  | `validate_llm_temperature` | `def validate_llm_temperature(cfg) -> None` | Validate that llm_temperature is in [0.0, LLM_TEMPERATURE_MAX]. |
|  | `validate_llm_max_tokens` | `def validate_llm_max_tokens(cfg) -> None` | Validate that llm_max_tokens is at least 1. |
|  | `validate_llm_sse_heartbeat_timeout` | `def validate_llm_sse_heartbeat_timeout(cfg) -> None` | Validate that sse_heartbeat_timeout is non-negative. |
|  | `validate_llm_sse_malformed_retry` | `def validate_llm_sse_malformed_retry(cfg) -> None` | Validate that sse_malformed_retry is a non-negative int. |
|  | `validate_llm_sse_reconnect_max` | `def validate_llm_sse_reconnect_max(cfg) -> None` | Validate that sse_reconnect_max is a non-negative int. |
|  | `check_agent_refiner_keys` | `def check_agent_refiner_keys(raw_cfg) -> list[str]` | Return an error when config/agent.toml still carries refiner keys. |
|  | `validate_tool_dedup_max_repeats` | `def validate_tool_dedup_max_repeats(cfg) -> None` | Validate that tool_dedup_max_repeats is at least 1. |
|  | `validate_tool_cycle_detect_window` | `def validate_tool_cycle_detect_window(cfg) -> None` | Validate that tool_cycle_detect_window is a non-negative int. |
|  | `validate_tool_error_max_consecutive` | `def validate_tool_error_max_consecutive(cfg) -> None` | Validate that tool_error_max_consecutive is a non-negative int. |
|  | `validate_tool_error_retry_max` | `def validate_tool_error_retry_max(cfg) -> None` | Validate that tool_error_retry_max is a non-negative int. |
|  | `validate_progress_stagnation_window` | `def validate_progress_stagnation_window(cfg) -> None` | Validate that progress_stagnation_window is a non-negative int. |
|  | `validate_allowed_tools` | `def validate_allowed_tools(cfg) -> None` | Validate that allowed_tools is a list of strings (an empty list is valid). |
|  | `validate_tool_policy_mode` | `def validate_tool_policy_mode(cfg) -> None` | Validate that tool_policy_mode is one of the allowed enum values. |
|  | `validate_disabled_tools` | `def validate_disabled_tools(cfg) -> None` | Validate that disabled_tools is a list of registered tool names. |
|  | `validate_memory_fts_limit` | `def validate_memory_fts_limit(cfg) -> None` | Validate that memory_fts_limit is at least 1. |
|  | `validate_memory_rrf_k` | `def validate_memory_rrf_k(cfg) -> None` | Validate that memory_rrf_k is at least 1. |
|  | `validate_memory_recency_days` | `def validate_memory_recency_days(cfg) -> None` | Validate that memory_recency_days is positive. |
|  | `validate_memory_max_inject_semantic` | `def validate_memory_max_inject_semantic(cfg) -> None` | Validate that memory_max_inject_semantic is a non-negative int. |
|  | `validate_memory_max_inject_episodic` | `def validate_memory_max_inject_episodic(cfg) -> None` | Validate that memory_max_inject_episodic is a non-negative int. |
|  | `validate_memory_embed_timeout_sec` | `def validate_memory_embed_timeout_sec(cfg) -> None` | Validate that memory_embed_timeout_sec is positive. |
|  | `validate_memory_retention_days` | `def validate_memory_retention_days(cfg) -> None` | Validate that memory_retention_days is at least 1. |
|  | `validate_memory_max_pinned` | `def validate_memory_max_pinned(cfg) -> None` | Validate that memory_max_pinned is at least 1. |
|  | `validate_diagnostics_encryption_key` | `def validate_diagnostics_encryption_key(cfg) -> None` | Validate encryption_key is a valid Fernet key when configured (empty = disabled). |
|  | `validate_diagnostics_retention_days` | `def validate_diagnostics_retention_days(cfg) -> None` | Validate retention_days is an int (<= 0 disables purge). |
|  | `validate_diagnostics_sensitive_fields` | `def validate_diagnostics_sensitive_fields(cfg) -> None` | Validate sensitive_fields is a frozenset of strings. |
|  | `validate_allowed_root` | `def validate_allowed_root(cfg) -> None` | Validate that allowed_root is a non-empty absolute path. |
|  | `validate_llm_http_timeout` | `def validate_llm_http_timeout(cfg) -> None` | Validate that http_timeout is positive. |
|  | `validate_llm_context_token_limit` | `def validate_llm_context_token_limit(cfg) -> None` | Validate that context_token_limit is a non-negative int. |
|  | `validate_tool_max_tool_turns` | `def validate_tool_max_tool_turns(cfg) -> None` | Validate that max_tool_turns is positive. |
|  | `validate_tool_result_max_llm_chars` | `def validate_tool_result_max_llm_chars(cfg) -> None` | Validate that tool_result_max_llm_chars is positive. |
|  | `validate_llm_url` | `def validate_llm_url(cfg) -> None` | Validate that llm_url is a string (an empty value means no LLM endpoint). |
|  | `validate_context_compress_turns` | `def validate_context_compress_turns(cfg) -> None` | Validate that context_compress_turns is an int. |
|  | `validate_llm_stream_retry_on_heartbeat_timeout` | `def validate_llm_stream_retry_on_heartbeat_timeout(cfg) -> None` | Validate that llm_stream_retry_on_heartbeat_timeout is a bool. |
|  | `validate_llm_stream_retry_on_malformed_chunk` | `def validate_llm_stream_retry_on_malformed_chunk(cfg) -> None` | Validate that llm_stream_retry_on_malformed_chunk is a bool. |
|  | `validate_serial_tool_calls` | `def validate_serial_tool_calls(cfg) -> None` | Validate that serial_tool_calls is a bool. |
|  | `validate_plan_blocked_tools` | `def validate_plan_blocked_tools(cfg) -> None` | Validate that plan_blocked_tools is a list of strings (an empty list is valid). |
|  | `validate_approval_protected_paths` | `def validate_approval_protected_paths(cfg) -> None` | Validate that approval_protected_paths is a list of strings (an empty list is valid). |
|  | `validate_approval_high_risk_branches` | `def validate_approval_high_risk_branches(cfg) -> None` | Validate that approval_high_risk_branches is a list of strings (an empty list is valid). |
|  | `validate_approval_shell_safe_prefixes` | `def validate_approval_shell_safe_prefixes(cfg) -> None` | Validate that approval_shell_safe_prefixes is a list of strings. |
|  | `validate_approval_github_allowed_repos` | `def validate_approval_github_allowed_repos(cfg) -> None` | Validate that approval_github_allowed_repos is a list of strings (an empty list is valid). |
|  | `validate_gitops_push_blocked` | `def validate_gitops_push_blocked(cfg) -> None` | Validate that gitops_push_blocked is a bool. |
|  | `validate_approval_medium_preview_fallback` | `def validate_approval_medium_preview_fallback(cfg) -> None` | Validate that approval_medium_preview_fallback is a bool. |
|  | `validate_memory_local_only` | `def validate_memory_local_only(cfg) -> None` | Validate that memory_local_only is a bool. |
|  | `validate_use_memory_layer` | `def validate_use_memory_layer(cfg) -> None` | Validate that use_memory_layer is a bool. |
|  | `validate_memory_embed_enabled` | `def validate_memory_embed_enabled(cfg) -> None` | Validate that memory_embed_enabled is a bool. |
|  | `validate_memory_embed_url` | `def validate_memory_embed_url(cfg) -> None` | Validate that memory_embed_url is a string. |
| `scripts/agent/services/context_view.py` | `budget_breakdown` | `def budget_breakdown(messages) -> ContextBudget` | Compute per-category character counts (system / history / tool_messages). |
|  | `collect_context_state` | `def collect_context_state(ctx) -> ContextStateView` | Aggregate runtime context data for /context display. |
| `scripts/agent/services/conversation_service.py` | `clear_conversation` | `async def clear_conversation(ctx, *, new_session) -> ConversationActionResult` | Reset in-memory conversation history to the system prompt and clear stats. |
| `scripts/agent/services/db_maintenance_service.py` | `DbMaintenanceService` | `class DbMaintenanceService` | Wraps maintenance operations on session.sqlite only. |
| `scripts/agent/services/enums.py` | `McpTier` | `class McpTier` | Security tier classification for MCP servers. |
|  | `McpAvailability` | `class McpAvailability` | Runtime availability state of an MCP server. |
|  | `ConversationActionType` | `class ConversationActionType` | Types of conversation-level actions that can be performed. |
|  | `ExportFormat` | `class ExportFormat` | Supported export formats for agent session data. |
| `scripts/agent/services/exceptions.py` | `McpProbeError` | `class McpProbeError` | Raised when an MCP server probe encounters an unrecoverable error. |
|  | `SessionTitleGenerationError` | `class SessionTitleGenerationError` | Raised when LLM-based session title generation fails. |
|  | `ConfigReloadError` | `class ConfigReloadError` | Base for configuration reload failures. |
|  | `ConfigReloadValidationError` | `class ConfigReloadValidationError` | Raised when a config reload request or candidate value fails a declared rule. |
|  | `ConfigReloadCommitError` | `class ConfigReloadCommitError` | Raised when a commit step failed after the transaction undid the applied steps. |
|  | `ConfigReloadRollbackError` | `class ConfigReloadRollbackError` | Raised when a rollback step failed, leaving live state inconsistent. |
|  | `ContextStateBuildError` | `class ContextStateBuildError` | Raised when context state cannot be built (e.g. hist_mgr is None). |
|  | `ExportWriteError` | `class ExportWriteError` | Raised when writing an export file fails. |
|  | `ConversationStateError` | `class ConversationStateError` | Raised when a conversation state operation fails (e.g. unknown prompt preset). |
|  | `DbMaintenanceError` | `class DbMaintenanceError` | Raised when a DB maintenance operation fails. |
|  | `SessionNotFoundError` | `class SessionNotFoundError` | Raised when a requested session does not exist or has no messages. |
|  | `SessionNoMessagesError` | `class SessionNoMessagesError` | Raised when a requested session exists but has no messages. |
|  | `NothingToUndoError` | `class NothingToUndoError` | Raised when undo is requested but no user message is in history. |
| `scripts/agent/services/export_formatter.py` | `fence_for` | `def fence_for(text) -> str` | The code fence that can close `text`: longest backtick run plus one, minimum three. |
|  | `escape_md` | `def escape_md(value) -> str` | Neutralise the Markdown structure a value could introduce in a heading line. |
|  | `render_history_md` | `def render_history_md(history) -> str` | Render conversation history as a Markdown export string with a closable fence. |
|  | `render_export` | `def render_export(history, fmt) -> str` | Render conversation history to a string in the requested format. |
|  | `write_export` | `def write_export(content, outfile, n_messages, out) -> None` | Write export content to stdout or a file. |
| `scripts/agent/services/io_ports.py` | `ExportOutputPort` | `class ExportOutputPort` | Output abstraction for conversation export operations. |
| `scripts/agent/services/maintenance_jobs.py` | `JobState` | `class JobState` | Lifecycle states of a maintenance run. |
|  | `ApprovalLevel` | `class ApprovalLevel` | Approval a run needs, declared with the operation rather than the command line. |
|  | `Cancelability` | `class Cancelability` | Whether SQLite can still interrupt the operation at its next progress callback. |
|  | `StoreTarget` | `class StoreTarget` | Target store a write job runs against; one running writer per store. |
|  | `JobConflictError` | `class JobConflictError` | Raised when a write job is registered against a store that has one running. |
|  | `MaintenanceJob` | `class MaintenanceJob` | One maintenance run as the registry records it. |
|  | `ApprovalDecision` | `class ApprovalDecision` | Result of the approval step for one run, recorded on the job. |
|  | `CancelResult` | `class CancelResult` | Result of a cancellation request, so the caller can state it instead of guessing. |
|  | `OperationProfile` | `class OperationProfile` | What the registry declares about one operation: level, cancelability, writer slot. |
|  | `profile_for` | `def profile_for(operation) -> OperationProfile` | Return the declared profile for one operation. |
|  | `MaintenanceJobRegistry` | `class MaintenanceJobRegistry` | Owner of the maintenance job records for one process. |
| `scripts/agent/services/mcp_health.py` | `ServerFailureClass` | `class ServerFailureClass` | Kind of MCP server failure. Availability is reachability; Safety and Integrity are posture. |
|  | `PostureGate` | `class PostureGate` | One server's permission to serve tools, decided from the posture it published. |
|  | `classify_server_failure` | `def classify_server_failure(gate) -> ServerFailureClass \| None` | Return the failure kind of one gate, or None when the gate is green. |
|  | `CapabilityFinding` | `class CapabilityFinding` | What one gate's parsed report proves about its capabilities. |
|  | `classify_capabilities` | `def classify_capabilities(gate, required_capability) -> CapabilityFinding` | Classify one gate's report for its required capability and its optional losses. |
|  | `collect_server_postures` | `async def collect_server_postures(ctx) -> dict[str, PostureGate]` | Probe every usable HTTP MCP server once and gate it on the posture it publishes. |
|  | `allowed_server_keys` | `def allowed_server_keys(gates) -> set[str]` | Server keys whose gate is fully green, for RuntimeToolRegistry(allowed_servers=...). |
|  | `check_service_health` | `async def check_service_health(ctx, *, gates) -> HealthCheckResult` | Probe LLM and Embed service health, then every MCP server posture, at startup. |
|  | `check_readiness` | `async def check_readiness(ctx, *, gates) -> HealthCheckResult` | Probe required services at startup; raise RuntimeError on required-service failure. |
| `scripts/agent/services/mcp_status.py` | `McpPendingRow` | `class McpPendingRow` | One MCP definition change `/mcp status` shows as pending, not as a live server. |
|  | `McpStatusService` | `class McpStatusService` | Probe all configured MCP servers and collect their health statuses. |
| `scripts/agent/services/mcp_tool_discovery.py` | `DiscoveryResult` | `class DiscoveryResult` | Result of discovering tools across all configured MCP servers. |
|  | `McpToolDiscoveryService` | `class McpToolDiscoveryService` | Discover live MCP tools and build a `RuntimeToolRegistry`. |
| `scripts/agent/services/models.py` | `ProcessInfoSnapshot` | `class ProcessInfoSnapshot` | Read-only snapshot of an HTTP MCP subprocess's runtime state. |
|  | `SessionTitleResult` | `class SessionTitleResult` | Result of generating a session title. |
|  | `McpProbeResult` | `class McpProbeResult` | Result of probing a single MCP server's health status. |
|  | `SessionRestoreResult` | `class SessionRestoreResult` | Result of restoring a session from the database. |
|  | `DeletedRow` | `class DeletedRow` | A single deleted message row's identity, returned by the DB-side undo. |
|  | `UndoResult` | `class UndoResult` | Result of undoing a conversation action. |
|  | `ConversationActionResult` | `class ConversationActionResult` | Result of executing a conversation action. |
|  | `ContextStateView` | `class ContextStateView` | Current context state view including character/token budgets and compression info. |
|  | `DbStats` | `class DbStats` | Database statistics including document, chunk, session, and message counts. |
|  | `DbHealth` | `class DbHealth` | Database health check result including integrity, WAL pages, and size. |
|  | `DbCheckpointResult` | `class DbCheckpointResult` | Result of a database checkpoint operation. |
|  | `DbVacuumResult` | `class DbVacuumResult` | Result of a vacuum run; the page counts are measured by the postcondition. |
|  | `DbPurgeResult` | `class DbPurgeResult` | Result of purging old sessions from the database. |
|  | `DbRecoverResult` | `class DbRecoverResult` | Result of a database recovery attempt. |
|  | `RagConsistencyResult` | `class RagConsistencyResult` | RAG consistency check result with issues, detailed report, and severity. |
|  | `RagFtsRebuildResult` | `class RagFtsRebuildResult` | Result of an FTS index rebuild, with the counts the postcondition measured. |
|  | `RagVecPruneResult` | `class RagVecPruneResult` | Result of the orphan-vector prune, with the counts the run measured. |
|  | `ExportResult` | `class ExportResult` | Result of exporting session data in a specific format. |
|  | `ConfigReloadRequest` | `class ConfigReloadRequest` | Typed request for apply_config. All fields optional; missing fields are skipped. |
|  | `SessionRow` | `class SessionRow` | One row from session.list_sessions(): session_id, title, created_at, is_current, message_count. |
|  | `ContextBudget` | `class ContextBudget` | Per-category character and token counts for /context budget breakdown. |
| `scripts/agent/services/posture_validator.py` | `PostureValidationResult` | `class PostureValidationResult` | One contract verdict the classification layer (row `18`) consumes. |
|  | `parse_posture` | `def parse_posture(body, server_key) -> PostureValidationResult` | Read the `security` block out of a /health body and validate what it holds. |
|  | `validate_posture` | `def validate_posture(posture, *, expected_server_key) -> PostureValidationResult` | Check a posture against the shared contract, in the fixed order the contract names. |
|  | `compare_fingerprint` | `def compare_fingerprint(server_key, posture) -> PostureValidationResult` | Report whether a server's fingerprint changed since the last posture seen for that key. |
|  | `reset_fingerprint_state` | `def reset_fingerprint_state() -> None` | Clear the process-local fingerprint map, for tests. |
| `scripts/agent/services/rag_maintenance_service.py` | `RagMaintenanceService` | `class RagMaintenanceService` | Maintenance operations scoped exclusively to rag.sqlite. |
| `scripts/agent/services/routing_drift.py` | `check_routing_safety_tiers` | `def check_routing_safety_tiers(ctx) -> list[str]` | Return tier-drift findings comparing the seed registry with live declarations. |
| `scripts/agent/services/session_restore.py` | `repair_orphan_tool_calls` | `def repair_orphan_tool_calls(messages, session_id, *, boundary_index) -> tuple[list[LLMMessage], int]` | Pair assistant tool_calls rows with tool-result rows at load time. |
|  | `RestoredSessionState` | `class RestoredSessionState` | State rebuilt from a stored session, ready to be committed atomically. |
|  | `restore_session` | `async def restore_session(ctx, session_id) -> RestoredSessionState` | Build the restored state of a stored session without mutating ``ctx``. |
| `scripts/agent/services/session_title.py` | `SessionTitleService` | `class SessionTitleService` | Generate a short LLM-based title for a session and persist it. |
| `scripts/agent/services/session_transition.py` | `SessionTransitionRefusedError` | `class SessionTransitionRefusedError` | Raised when a transition is requested while a turn is running. |
|  | `SessionTransitionSnapshot` | `class SessionTransitionSnapshot` | Immutable copy of every field a transition commit changes. |
|  | `SessionTransitionService` | `class SessionTransitionService` | Runs ``/clear new`` and ``/session load`` as one atomic transition. |
| `scripts/agent/services/tool_validation.py` | `check_tool_definitions_runtime` | `async def check_tool_definitions_runtime(ctx) -> HealthCheckResult` | Runtime validation: no raise, warnings only. |
| `scripts/agent/services/undo_service.py` | `UndoReloadError` | `class UndoReloadError` | Raised when the memory reload after the undo DB delete failed. |
|  | `undo_last_turn` | `def undo_last_turn(ctx) -> UndoResult` | Roll back the last user+assistant turn, gated by the compression boundary. |
| `scripts/agent/services/workflow_schema.py` | `check_workflow_definition` | `def check_workflow_definition(workflows_dir) -> None` | Raise RuntimeError if the workflow definition file is missing or invalid. |
|  | `SchemaCheckResult` | `class SchemaCheckResult` | Result of a workflow schema check. |
|  | `check_workflow_schema` | `def check_workflow_schema(db_config, db_path) -> SchemaCheckResult` | Return SchemaCheckResult indicating whether the workflow DB schema is valid. |
| `scripts/agent/shared/health_models.py` | `ServiceWarning` | `class ServiceWarning` | A warning about a service during startup validation. |
|  | `HealthCheckResult` | `class HealthCheckResult` | Aggregated health check results with warnings and errors. |
|  | `McpHealthProbeResult` | `class McpHealthProbeResult` | Structured result of a single /health GET probe to an MCP server. |
|  | `StartupCheckStatus` | `class StartupCheckStatus` | Status of a startup validation check. |
|  | `StartupCheckOutcome` | `class StartupCheckOutcome` | Result of a single startup validation check. |
|  | `StartupValidationResult` | `class StartupValidationResult` | Aggregated startup validation results across all checks. |
|  | `HealthInterpretation` | `class HealthInterpretation` | Structured interpretation of a raw /health response body dict. |
|  | `interpret_health_body` | `def interpret_health_body(body) -> HealthInterpretation` | Interpret a raw /health JSON body into structured fields. |
|  | `extract_health_reason` | `def extract_health_reason(body) -> str \| None` | Extract a human-readable reason string from a /health body. |
|  | `summarize_dependencies` | `def summarize_dependencies(deps) -> list[str]` | Summarise dependency statuses, returning only failed required ones. |
|  | `summarize_details` | `def summarize_details(details) -> list[str]` | Summarise detail entries, truncating large payloads. |
| `scripts/agent/shared/models.py` | `ToolApprovalEvent` | `class ToolApprovalEvent` | Structured audit event for tool_approval log entries. |
|  | `ToolExecEvent` | `class ToolExecEvent` | Structured audit event for tool_exec log entries. |
|  | `ApprovalGrant` | `class ApprovalGrant` | Proof that the approval gate authorized one specific prepared call. |
| `scripts/agent/shared/retry_helper.py` | `retry_once_with_delay` | `async def retry_once_with_delay(fn, delay, shutdown_event, interrupt_msg, *, skip_first_attempt, fatal_prefix) -> T` | Execute *fn* once; if it raises, wait *delay* seconds and retry once. |
| `scripts/agent/workflow/artifact_ops.py` | `record_artifact` | `def record_artifact(db, task_id, stage_id, uri, workflow_id, attempt_number) -> ArtifactRef` | Insert an artifact reference into the database and return it. |
| `scripts/agent/workflow/attempt_ops.py` | `get_owner_id` | `def get_owner_id() -> str` | Return this process's owner identity: hostname-pid-random. |
|  | `lease_expires_from` | `def lease_expires_from(started_at, lease_duration_sec) -> str` | Derive the lease deadline from a production timestamp plus a duration. |
|  | `finish_attempt` | `def finish_attempt(db, attempt_id, status, error_msg, error_kind, error_detail) -> None` | Mark an attempt as completed with the given status and optional error details. |
| `scripts/agent/workflow/idempotency_ops.py` | `is_event_processed` | `def is_event_processed(db, event_id) -> bool` | Check whether an event has already been processed by looking up its ID. |
|  | `begin_stage_if_new` | `def begin_stage_if_new(db, event_id, task_id, stage_id, lease_duration_sec, workflow_id) -> AttemptRecord \| None` | Atomically check event_id and start attempt if new. |
| `scripts/agent/workflow/models.py` | `TaskRecord` | `class TaskRecord` | Database record for a workflow task execution. |
|  | `AttemptRecord` | `class AttemptRecord` | Database record for a single stage attempt within a task. |
|  | `ArtifactRef` | `class ArtifactRef` | Reference to an artifact produced by a stage execution. |
|  | `StageDefinition` | `class StageDefinition` | A single stage in a workflow definition. |
|  | `RetryPolicy` | `class RetryPolicy` | Retry policy configuration for a workflow. |
|  | `WorkflowDef` | `class WorkflowDef` | Workflow definition with stages and retry configuration. |
| `scripts/agent/workflow/state_store.py` | `RecoveryReport` | `class RecoveryReport` | Classification counts from the last ``recover_stale_attempts()`` run. |
|  | `StateStore` | `class StateStore` | CRUD facade over workflow.sqlite. One instance per workflow engine lifecycle. |
| `scripts/agent/workflow/task_ops.py` | `create_task` | `def create_task(db, session_id, turn_number, workflow_version, workflow_id) -> TaskRecord` | Create a new task record. |
|  | `update_task_status` | `def update_task_status(db, task_id, status, *, commit) -> None` | Update the status of a task record in the database. |
|  | `get_task_by_id` | `def get_task_by_id(db, task_id) -> TaskRecord \| None` | Return the task record for the given task_id, or None if absent. |
|  | `get_task_count` | `def get_task_count(db, session_id) -> int` | Return the number of tasks associated with a session. |
|  | `get_workflow_count` | `def get_workflow_count(db, session_id) -> int` | Return the number of distinct workflows for a session. |
| `scripts/agent/workflow/tool_call_state_ops.py` | `ToolCallState` | `class ToolCallState` | Database record for one tool-call lifecycle row. |
|  | `CallStateResolver` | `class CallStateResolver` | The seam stale classification consults for an already-dispatched row. |
|  | `record_tool_call` | `def record_tool_call(db, task_id, idempotency_key, tool, retry_class, args_hash) -> None` | Insert a tool-call row in state 'pending'. |
|  | `finalize_tool_call` | `def finalize_tool_call(db, idempotency_key, state) -> None` | Move a tool-call row to another state in the intent vocabulary, bumping |
|  | `pending_tool_calls` | `def pending_tool_calls(db, task_id) -> list[ToolCallState]` | Return the task's pending tool-call rows, oldest first. |
|  | `classify_stale_pending` | `def classify_stale_pending(db, task_id, timeout_seconds, resolver) -> list[ToolCallState]` | Transition this task's timed-out tool-call rows by dispatch stage. |
|  | `reconstruct_replay_directives` | `def reconstruct_replay_directives(db, task_id) -> list[ToolCallState]` | Return this task's `interrupted` replayable rows, oldest first. |
|  | `get_tool_call_state` | `def get_tool_call_state(db, idempotency_key) -> ToolCallState \| None` | Return one tool-call row by key, or None if absent. |
| `scripts/agent/workflow/validate.py` | `validate_path` | `def validate_path(path) -> WorkflowDef` | Return the loaded WorkflowDef, or raise WorkflowLoadError if invalid. |
|  | `main` | `def main() -> int` | Validate a workflow definition JSON file against the schema. |
| `scripts/agent/workflow/workflow_engine.py` | `WorkflowHaltError` | `class WorkflowHaltError` | Raised when a task exceeds max_attempts and is halted. |
|  | `WorkflowTimeoutError` | `class WorkflowTimeoutError` | Raised when a stage exceeds its timeout_sec. |
|  | `WorkflowStageFailure` | `class WorkflowStageFailure` | Raised when a stage callback reports a typed failure result (kind llm_failure). |
|  | `WorkflowStageNotFoundError` | `class WorkflowStageNotFoundError` | Raised when a requested stage_id has no StageDefinition in the loaded workflow. |
|  | `TurnControl` | `class TurnControl` | Turn-entry control report: the LLM-facing text plus the Agent-side directives. |
|  | `WorkflowEngine` | `class WorkflowEngine` | Runs a workflow definition against a set of stage callbacks. |
| `scripts/agent/workflow/workflow_loader.py` | `WorkflowLoadError` | `class WorkflowLoadError` | Raised when a workflow JSON file cannot be loaded or fails validation. |
|  | `WorkflowLoader` | `class WorkflowLoader` | Loads a WorkflowDef from a JSON file in config/workflows/. |
<!-- END AUTO-GENERATED -->
