---
title: "Agent Reference API — Generated Class/Function Index"
area: agent
tags:
  - agent
  - api-reference
  - generated
related:
  - 05_agent_13_reference-api.md
---

# Agent Reference API — Generated Class/Function Index

## Purpose

Generated index of every public top-level class/function under
`scripts/agent/*.py` (`tools/generate_reference_table.py --type agent`).
Companion to [05_agent_13_reference-api.md](05_agent_13_reference-api.md)
(hand-curated); split into its own file to stay under the per-document size
threshold. Do not hand-edit between the guard comments — run the generator.

## Related Documents

- [05_agent_13_reference-api.md](05_agent_13_reference-api.md) — hand-curated Agent API reference
- [00_governance_01_documentation-policy.md](00_governance_01_documentation-policy.md) — ADR-015 Reference Document Class Disposition

## Keywords

agent, api-reference, generated

## Module Class/Function Reference (auto-generated)

<!-- AUTO-GENERATED: gen_agent_reference.py class-function-reference -->
Generated from `scripts/agent/*.py` top-level public classes and functions. Do not hand-edit between the guard comments; run `python tools/generate_reference_table.py --type agent` to refresh.

| File | Class/Function | Signature | Summary |
|---|---|---|---|
| `scripts/agent/audit_event_emitter.py` | `format_session_id` | `def format_session_id(session_id) -> str` | Format session_id for audit logs, returning empty string when None. |
|  | `AuditEventEmitter` | `class AuditEventEmitter` | Constructs and emits audit events for turn lifecycle boundaries. |
| `scripts/agent/bg_task_monitor.py` | `BgTaskMonitor` | `class BgTaskMonitor` | Monitors background task failures and enforces threshold-based policies. |
| `scripts/agent/cli_view.py` | `WriterBase` | `class WriterBase` | Base class providing default implementations for output methods. |
|  | `Reader` | `class Reader` | Input-side interface for multiline continuation prompts. |
|  | `CLIView` | `class CLIView` | Manages terminal I/O: readline history, tab completion, multiline |
| `scripts/agent/config_builders.py` | `load_config` | `def load_config() -> dict[str, Any]` | Load configuration from files.  No module-level cache — always fresh. |
|  | `build_agent_config` | `def build_agent_config(cfg_override) -> AgentConfig` | Construct AgentConfig from a config dict. |
| `scripts/agent/config_dataclasses.py` | `LLMConfig` | `class LLMConfig` | LLM communication and context management settings. |
|  | `RAGConfig` | `class RAGConfig` | RAG pipeline and vector search settings. |
|  | `ToolConfig` | `class ToolConfig` | Tool execution, approval policy, and prompt settings. |
|  | `MemoryConfig` | `class MemoryConfig` | Persistent semantic memory layer settings. |
|  | `MCPConfig` | `class MCPConfig` | MCP server lifecycle settings. |
|  | `ApprovalConfig` | `class ApprovalConfig` | Risk-based tool approval policy settings. |
|  | `ObservabilityConfig` | `class ObservabilityConfig` | OpenTelemetry tracing, audit logging, and structured log settings. |
|  | `DiagnosticsConfig` | `class DiagnosticsConfig` | Diagnostic storage encryption and retention settings. |
|  | `MessageRoleConfig` | `class MessageRoleConfig` | Valid message roles for SessionMessageRepository. |
|  | `AgentConfig` | `class AgentConfig` | Mutable runtime configuration shared by all agent components. |
| `scripts/agent/context.py` | `ConversationState` | `class ConversationState` | Per-session conversation fields. |
|  | `TurnState` | `class TurnState` | Per-turn transient state; reset each turn by Orchestrator. |
|  | `RuntimeStats` | `class RuntimeStats` | Accumulated session statistics. |
|  | `WorkflowState` | `class WorkflowState` | Per-session workflow runtime state; transient, not persisted. |
|  | `AppServices` | `class AppServices` | Fully-initialized service references built by factory.py. |
|  | `AgentContext` | `class AgentContext` | Mutable runtime state shared between AgentREPL and CommandRegistry. |
| `scripts/agent/conversation_state_manager.py` | `ConversationStateManager` | `class ConversationStateManager` | Manages conversation history state across turns. |
| `scripts/agent/diagnostic_store.py` | `DiagnosticStore` | `class DiagnosticStore` | Dedicated store for diagnostic messages, separate from conversation history. |
| `scripts/agent/error_injection_service.py` | `ErrorInjectionService` | `class ErrorInjectionService` | Service for handling synthetic error injection in agent turns. |
| `scripts/agent/factory.py` | `init_tracer` | `def init_tracer(ctx) -> object` | Build and return an OTel tracer; returns a NoOp stub when otel_enabled=False. |
|  | `build_agent_context` | `def build_agent_context(ctx, view) -> None` | Inject all services into ctx.services. |
| `scripts/agent/history.py` | `HistoryCompressionError` | `class HistoryCompressionError` | Raised when LLM-based history compression fails. |
|  | `CompressResult` | `class CompressResult` | Metadata returned by compress() and force_compress(). |
|  | `HistoryManager` | `class HistoryManager` | Manages conversation history size via LLM-based compression. |
| `scripts/agent/history_selection_policy.py` | `SelectionResult` | `class SelectionResult` | Typed result of select_turns_to_compress(). |
|  | `HistorySelectionPolicy` | `class HistorySelectionPolicy` | Determines which messages to compress based on importance scoring. |
| `scripts/agent/http_lifecycle.py` | `HttpServerLifecycleManager` | `class HttpServerLifecycleManager` | Manages HTTP subprocess MCP servers: start, health-poll, restart, shutdown. |
| `scripts/agent/http_lifecycle_command_validator.py` | `CommandValidator` | `class CommandValidator` | Validates commands and filters environment variables for HTTP subprocess MCP servers. |
| `scripts/agent/http_lifecycle_errors.py` | `StartupFailure` | `class StartupFailure` | Records the full stderr output and reason when an HTTP subprocess fails to start. |
|  | `HttpStartupError` | `class HttpStartupError` | Raised when an HTTP subprocess MCP server fails to start. |
| `scripts/agent/http_lifecycle_health_checker.py` | `HealthChecker` | `class HealthChecker` | Performs HTTP health checks against a running server. |
|  | `ProcessSnapshotProvider` | `class ProcessSnapshotProvider` | Provides process snapshots via /proc filesystem access. |
| `scripts/agent/http_lifecycle_process_terminator.py` | `ProcessTerminator` | `class ProcessTerminator` | Manages process termination with SIGTERM → SIGKILL escalation. |
| `scripts/agent/http_lifecycle_shutdown_coordinator.py` | `ShutdownCoordinator` | `class ShutdownCoordinator` | Coordinates shutdown of HTTP server process and associated resources. |
| `scripts/agent/http_lifecycle_stderr_log_manager.py` | `StderrLogManager` | `class StderrLogManager` | Manages stderr log files for HTTP subprocess MCP servers. |
| `scripts/agent/lifecycle.py` | `LifecycleState` | `class LifecycleState` | Transport state for HTTP MCP servers. |
|  | `assert_valid_transition` | `def assert_valid_transition(from_state, to_state) -> None` | Raise ValueError when the transition from_state -> to_state is not legal. |
| `scripts/agent/lifecycle_protocol.py` | `LifecycleManagerProtocol` | `class LifecycleManagerProtocol` | Protocol for MCP server lifecycle managers. |
| `scripts/agent/llm_transport_errors.py` | `handle_llm_transport_error` | `def handle_llm_transport_error(e, ctx, diagnostic_store) -> bool` | Handle LLM transport error: partial or non-partial. |
|  | `handle_partial_completion` | `def handle_partial_completion(e, ctx, diagnostic_store) -> None` | Save partial text to diagnostic channel only. |
|  | `handle_non_partial_error` | `def handle_non_partial_error(e, ctx, diagnostic_store) -> None` | Save non-partial error to diagnostic channel and log. |
| `scripts/agent/llm_turn_executor.py` | `LlmTurnExecutor` | `class LlmTurnExecutor` | Executes an LLM turn: streaming + inner tool-call loop. |
| `scripts/agent/llm_turn_runner.py` | `LLMTurnRunner` | `class LLMTurnRunner` | Legacy alias for `LlmTurnExecutor`; kept for backward compatibility during transition. |
| `scripts/agent/mdq_rag_classifier.py` | `MdqRagMode` | `class MdqRagMode` | Mode for selecting between MDQ and RAG search strategies. |
|  | `classify_query` | `def classify_query(query) -> MdqRagMode` | Return MDQ if query contains Markdown-structural terms; RAG otherwise. |
|  | `resolve_mode` | `def resolve_mode(query, config_mode) -> MdqRagMode` | Config override takes precedence; AUTO falls back to classifier heuristics. |
| `scripts/agent/message_schema.py` | `ValidationResult` | `class ValidationResult` | Result of message schema validation. |
|  | `validate_message` | `def validate_message(msg) -> ValidationResult` | Validate *msg* against the strict schema. |
|  | `is_trusted_source` | `def is_trusted_source(source_id) -> bool` | Check if *source_id* is authorized to inject ephemeral keys. |
|  | `get_allowed_ephemeral_keys` | `def get_allowed_ephemeral_keys(source_id) -> set[str]` | Get ephemeral keys allowed for a trusted source. |
| `scripts/agent/mode_classification.py` | `classify_and_inject_mode` | `async def classify_and_inject_mode(query, ctx) -> None` | Inject MDQ/RAG routing hint into system prompt based on query classification. |
| `scripts/agent/orchestrator.py` | `Orchestrator` | `class Orchestrator` | Turn-level coordinator: compression -> LLM loop -> tool dispatch. |
| `scripts/agent/output_tags.py` | `OutputTag` | `class OutputTag` | Bracketed prefix tags for REPL/CLI status messages. |
| `scripts/agent/repl.py` | `builtin_command_names` | `def builtin_command_names() -> frozenset[str]` | Return names of all built-in commands from _COMMANDS. |
|  | `reserved_repl_command_names` | `def reserved_repl_command_names() -> frozenset[str]` | Return names of REPL-reserved commands. |
|  | `completion_command_names` | `def completion_command_names() -> frozenset[str]` | Return all commands available for tab completion. |
|  | `AgentREPL` | `class AgentREPL` | Thin composition facade over extracted REPL concern classes. |
|  | `main` | `def main() -> None` | Start the interactive REPL. |
| `scripts/agent/repl_input_loop.py` | `ReplInputLoop` | `class ReplInputLoop` | Manages REPL input reading, dispatch, and exit conditions. |
| `scripts/agent/repository_gateway.py` | `RepositoryGateway` | `class RepositoryGateway` | Single write enforcement boundary for all repository mutation operations. |
| `scripts/agent/resource_shutdown_coordinator.py` | `ResourceShutdownCoordinator` | `class ResourceShutdownCoordinator` | Coordinates resource shutdown across all subsystems. |
| `scripts/agent/security_audit_config.py` | `ShellAuditConfig` | `class ShellAuditConfig` | Security audit configuration for shell command execution. |
|  | `GitAuditConfig` | `class GitAuditConfig` | Security audit configuration for git operations. |
|  | `GitHubAuditConfig` | `class GitHubAuditConfig` | Security audit configuration for GitHub API operations. |
|  | `CicdAuditConfig` | `class CicdAuditConfig` | Security audit configuration for CI/CD pipeline operations. |
|  | `load_shell_audit_config` | `def load_shell_audit_config() -> ShellAuditConfig \| None` | Load shell config for audit. Returns None if not installed. |
|  | `load_git_audit_config` | `def load_git_audit_config() -> GitAuditConfig \| None` | Load git config for audit. Returns None if not installed. |
|  | `load_github_audit_config` | `def load_github_audit_config() -> GitHubAuditConfig \| None` | Load GitHub config for audit. Returns None if not installed. |
|  | `load_cicd_audit_config` | `def load_cicd_audit_config() -> CicdAuditConfig \| None` | Load CI/CD config for audit. Returns None if not installed. |
| `scripts/agent/session.py` | `SchemaMissingError` | `class SchemaMissingError` | Raised when required SQLite schema tables are missing. |
|  | `AgentSession` | `class AgentSession` | Manages REPL session and message persistence in SQLite. |
| `scripts/agent/session_message_repo.py` | `SessionMessageRepository` | `class SessionMessageRepository` | Repository for session message operations. |
| `scripts/agent/session_persister.py` | `SessionPersister` | `class SessionPersister` | Handles persistence of session-level data at shutdown. |
| `scripts/agent/signal_handler.py` | `SignalHandler` | `class SignalHandler` | Encapsulates platform-specific signal handling for graceful shutdown. |
| `scripts/agent/startup.py` | `StartupInterrupted` | `class StartupInterrupted` | Raised when a SIGINT/SIGTERM shutdown request interrupts the startup sequence. |
|  | `StartupOrchestrator` | `class StartupOrchestrator` | Runs the full agent startup sequence before the REPL input loop begins. |
| `scripts/agent/startup_approval_recovery.py` | `ApprovalRecovery` | `class ApprovalRecovery` | Owns approval recovery from previous sessions. |
| `scripts/agent/startup_banner.py` | `StartupBanner` | `class StartupBanner` | Handles startup display and banner printing. |
| `scripts/agent/startup_component_init.py` | `ComponentInitializer` | `class ComponentInitializer` | Owns DI wiring, command registry init, orchestrator construction, and workflow preflight. |
| `scripts/agent/startup_mcp_starter.py` | `McpServerStarter` | `class McpServerStarter` | Owns MCP subprocess startup, health verification, and retry-once-with-delay. |
| `scripts/agent/startup_prompt_setup.py` | `PromptSetup` | `class PromptSetup` | Owns system prompt and memory setup. |
| `scripts/agent/startup_reporter.py` | `ReadinessReporter` | `class ReadinessReporter` | Owns pipeline result display and readiness reporting. |
| `scripts/agent/startup_validation.py` | `StartupValidationPipeline` | `class StartupValidationPipeline` | Owns the full service-validation pipeline. |
| `scripts/agent/tool_approval.py` | `check_approval` | `async def check_approval(ctx, tool_name, args) -> bool` | Return True when the tool call may proceed. |
|  | `run_approval_checks` | `async def run_approval_checks(ctx, prepared_calls) -> tuple[list[PreparedToolCall], list[str]]` | Run plan-mode block and interactive approval for each prepared tool call. |
| `scripts/agent/tool_arg_validator.py` | `ValidationResult` | `class ValidationResult` | Result of validating tool call arguments against an MCP input schema. |
|  | `validate_tool_arguments` | `def validate_tool_arguments(tool_name, args, input_schema, allow_extra_fields) -> ValidationResult` | Validate tool call arguments against the MCP tool's input schema. |
|  | `register_custom_validator` | `def register_custom_validator(tool_name) -> Callable[[CustomValidator], CustomValidator]` | Decorator that registers a custom validation hook for tool_name. |
| `scripts/agent/tool_audit.py` | `audit_approval` | `def audit_approval(ctx, tool_name, risk, args, decision) -> None` | Write a structured tool_approval event to the audit log. |
|  | `log_approval_decision` | `def log_approval_decision(ctx, outcome) -> None` | Write a structured approval_decision event to the audit log. |
|  | `audit_workflow_start` | `def audit_workflow_start(ctx, task_id, workflow_version, workflow_id, session_id) -> None` | Write workflow_start event to audit log. |
|  | `audit_stage_completed` | `def audit_stage_completed(ctx, task_id, stage_id, elapsed_ms, workflow_id, session_id) -> None` | Write stage_completed event to audit log. |
|  | `audit_approval_requested` | `def audit_approval_requested(ctx, task_id, approval_id, workflow_id, session_id) -> None` | Write approval_requested event to audit log. |
|  | `audit_tool_exec` | `def audit_tool_exec(ctx, tool_name, args, is_error, mcp_request_id, error_type, artifact_uri, source, idempotency_key, task_linkage) -> None` | Write a tool_exec event with mcp_request_id to the audit log. |
|  | `write_round_exec` | `def write_round_exec(ctx, *, round_id, tool_count, mode, has_side_effect, trigger_tool, elapsed_ms, affected_tools, serial_reason, estimated_parallel_ms, scheduling_mode) -> None` | Log a round-wide execution event, capturing serialization impact. |
| `scripts/agent/tool_enums.py` | `RiskLevel` | `class RiskLevel` | Risk level classification for tool operations. |
|  | `OperationType` | `class OperationType` | Categorization of tool operation kinds. |
|  | `ApprovalDecisionType` | `class ApprovalDecisionType` | Possible outcomes of an approval gate evaluation. |
|  | `GuardDecisionType` | `class GuardDecisionType` | Decisions made by the tool guardrail system. |
| `scripts/agent/tool_exceptions.py` | `ToolArgumentsDecodeError` | `class ToolArgumentsDecodeError` | Raised when tool call arguments cannot be decoded as JSON. |
|  | `ToolExecutorUnavailableError` | `class ToolExecutorUnavailableError` | Raised when ctx.services.tools is None at execution time. |
|  | `PolicyViolationError` | `class PolicyViolationError` | Raised when a pre-flight policy check denies the tool call. |
|  | `ApprovalPreviewError` | `class ApprovalPreviewError` | Raised when dry-run preview execution fails. |
|  | `ApprovalPreviewBlockingError` | `class ApprovalPreviewBlockingError` | Raised when dry-run preview returns an explicit error result. |
|  | `AuditUnavailableError` | `class AuditUnavailableError` | Defined for completeness; not raised — silent return is the policy |
|  | `LifecycleConfigurationError` | `class LifecycleConfigurationError` | Raised when a lifecycle operation is attempted with missing configuration. |
| `scripts/agent/tool_loop_guard.py` | `TurnLoopState` | `class TurnLoopState` | Mutable per-turn loop state passed through each inner turn. |
|  | `ToolLoopGuard` | `class ToolLoopGuard` | Guards the tool-call loop against dedup, cycle, retry, consecutive errors, and progress stagnation. |
| `scripts/agent/tool_models.py` | `ToolCallRequest` | `class ToolCallRequest` | Parsed, validated representation of a single LLM tool call. |
|  | `ToolMeta` | `class ToolMeta` | Scheduling metadata for a single tool. |
|  | `ToolExecutionResult` | `class ToolExecutionResult` | Result of executing one tool call. |
|  | `ApprovalOutcome` | `class ApprovalOutcome` | Structured result of a single tool approval evaluation. |
|  | `GuardDecision` | `class GuardDecision` | Result of a tool-loop guard check. |
| `scripts/agent/tool_output.py` | `emit_tool_call` | `def emit_tool_call(name, args_json, output) -> None` | Write a tool invocation line. |
|  | `emit_tool_result` | `def emit_tool_result(name, display, output) -> None` | Write a tool result summary line. |
|  | `emit_approval_prompt` | `def emit_approval_prompt(risk, tool_name, preview, output) -> None` | Write the approval prompt header and preview. |
|  | `emit_denied` | `def emit_denied(reason, output) -> None` | Write the denial line for a tool call. `reason` must include the tool name. |
|  | `emit_plan_blocked` | `def emit_plan_blocked(tool_name, args_json, output) -> None` | Write plan-mode block notification. |
|  | `emit_skipped` | `def emit_skipped(tool_name, output) -> None` | Write the 'skipped' confirmation after user denies a tool call. |
|  | `emit_approval_pending_notice` | `def emit_approval_pending_notice(approval_id, task_id, output) -> None` | Write a visible terminal notice when a workflow turn is suspended for approval. |
| `scripts/agent/tool_policy.py` | `classify_operation_type` | `def classify_operation_type(tool_name, registry) -> OperationType` | Return the operation type for a tool. |
|  | `classify_risk` | `def classify_risk(cfg, tool_name, args, registry) -> RiskLevel` | Return the risk level for a tool call. |
|  | `check_allowed_root` | `def check_allowed_root(cfg, tool_name, args) -> bool` | Return False when any path argument is outside cfg.approval.allowed_root. |
|  | `check_allowed_repo` | `def check_allowed_repo(cfg, tool_name, args) -> bool` | Return False when a GitHub write tool targets a repo not in the allowlist. |
|  | `check_preflight` | `def check_preflight(cfg, tool_name, args) -> None` | Raise PolicyViolationError when a pre-flight check denies the tool call. |
| `scripts/agent/tool_preparation.py` | `PreparedToolCall` | `class PreparedToolCall` | A raw tool call that has passed preparation and is ready for approval/execution. |
|  | `prepare_tool_calls` | `def prepare_tool_calls(ctx, tool_calls) -> tuple[list[PreparedToolCall], list[_PrepFailure]]` | Prepare a batch of raw tool calls, in order. |
| `scripts/agent/tool_result_formatter.py` | `turn_limit_hint` | `def turn_limit_hint(omitted_chars, omitted_lines, limit) -> str` | Build the hint shown to the LLM in place of a tool result dropped for |
|  | `mask_args` | `def mask_args(args, masked_fields) -> dict[str, Any]` | Return a copy of args with masked_fields values replaced by '***'. |
|  | `build_github_preview` | `def build_github_preview(args) -> str` | Build preview string for github_* tools showing repo and extra args. |
|  | `build_preview` | `def build_preview(tool_name, args) -> str` | Build a human-readable operation preview shown before approval prompts. |
| `scripts/agent/tool_runner.py` | `get_serialization_stats` | `def get_serialization_stats() -> dict[str, int]` | Return current serialization statistics. |
|  | `execute_one_tool_call` | `async def execute_one_tool_call(ctx, pc, turn) -> tuple[str, str, dict, str, bool, str]` | Execute and truncate one already-prepared tool call. |
|  | `execute_all_tool_calls` | `async def execute_all_tool_calls(ctx, tool_calls, turn, out_failed_keys) -> None` | Execute all tool calls then append results in original order. |
| `scripts/agent/tool_scheduler.py` | `MissingToolSpecError` | `class MissingToolSpecError` | Raised when a tool call's call_id has no entry in the call_specs map |
|  | `SerializationEvent` | `class SerializationEvent` | Record of one serialization decision made while building an ExecutionPlan. |
|  | `ScheduledGroup` | `class ScheduledGroup` | One group of calls within a batch. |
|  | `ScheduledBatch` | `class ScheduledBatch` | One or more ScheduledGroups that run concurrently with each other. |
|  | `ExecutionPlan` | `class ExecutionPlan` | The full scheduling result for one batch of tool calls. |
|  | `build_execution_groups` | `def build_execution_groups(tool_calls, call_specs, *, force_serial) -> ExecutionPlan` | Build the single-engine DAG execution plan for *tool_calls*. |
| `scripts/agent/turn_result.py` | `TurnResult` | `class TurnResult` | Typed result of one LLM turn. |
| `scripts/agent/turnd_coordinator.py` | `TurnCoordinator` | `class TurnCoordinator` | Coordinates per-turn lifecycle: start/end audit events only. |
| `scripts/agent/wal_checkpoint_manager.py` | `WalCheckpointManager` | `class WalCheckpointManager` | WAL checkpoint and backup manager. |
| `scripts/agent/workflow_engine_adapter.py` | `WorkflowEngineAdapter` | `class WorkflowEngineAdapter` | Wires workflow engine lifecycle around an LLM turn. |
<!-- END AUTO-GENERATED -->
