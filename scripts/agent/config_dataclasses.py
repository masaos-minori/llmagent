#!/usr/bin/env python3
"""agent/config_dataclasses.py

All configuration dataclass definitions for the agent pipeline.

Defines:
  LLMConfig       - LLM communication and context management settings
  RAGConfig       - RAG pipeline and vector search settings
  ToolConfig      - Tool execution, caching, approval policy, and prompt settings
  MemoryConfig    - Persistent semantic memory layer settings
  MCPConfig       - MCP server lifecycle and watchdog settings
  ApprovalConfig  - Risk-based tool approval policy settings
  ObservabilityConfig - OpenTelemetry tracing, audit logging, and structured log settings
  AgentConfig     - Composite: composes 7 domain-specific sub-configs

Import from here:  from agent.config_dataclasses import AgentConfig, LLMConfig, ...
"""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.mcp_config import McpServerConfig, SecurityProfile

from agent.services.config_validators import (
    validate_approval_risk_rules as _v_app_risk,
)
from agent.services.config_validators import (
    validate_llm_budget_warn_ratio as _v_llm_bwr,
)
from agent.services.config_validators import (
    validate_llm_context_char_limit as _v_llm_ccl,
)
from agent.services.config_validators import (
    validate_llm_max_retries as _v_llm_mr,
)
from agent.services.config_validators import (
    validate_llm_max_tokens as _v_llm_mt,
)
from agent.services.config_validators import (
    validate_llm_retry_base_delay as _v_llm_rbd,
)
from agent.services.config_validators import (
    validate_llm_sse_heartbeat_timeout as _v_llm_shrt,
)
from agent.services.config_validators import (
    validate_llm_sse_malformed_retry as _v_llm_smr,
)
from agent.services.config_validators import (
    validate_llm_sse_reconnect_max as _v_llm_srm,
)
from agent.services.config_validators import (
    validate_llm_temperature as _v_llm_temp,
)
from agent.services.config_validators import (
    validate_memory_fts_limit as _v_mem_fts,
)
from agent.services.config_validators import (
    validate_memory_recency_days as _v_mem_rec,
)
from agent.services.config_validators import (
    validate_memory_rrf_k as _v_mem_rrf,
)
from agent.services.config_validators import (
    validate_rag_refiner_max_chars_per_chunk as _v_rag_rmcc,
)
from agent.services.config_validators import (
    validate_rag_refiner_max_tokens as _v_rag_rmt,
)
from agent.services.config_validators import (
    validate_rag_refiner_timeout as _v_rag_rt,
)
from agent.services.config_validators import (
    validate_tool_cache_max_size as _v_tool_cms,
)
from agent.services.config_validators import (
    validate_tool_cycle_detect_window as _v_tool_cdw,
)
from agent.services.config_validators import (
    validate_tool_dedup_max_repeats as _v_tool_dm,
)
from agent.services.config_validators import (
    validate_tool_error_max_consecutive as _v_tool_emc,
)
from agent.services.config_validators import (
    validate_tool_error_retry_max as _v_tool_erm,
)
from agent.services.config_validators import (
    validate_tool_plugin_strict as _v_tool_ps,
)
from agent.services.config_validators import (
    validate_tool_plugin_tool_override as _v_tool_pto,
)
from agent.services.config_validators import (
    validate_tool_safety_tiers as _v_app_tier,
)

LLM_TEMPERATURE_MAX = 2.0


@dataclass
class LLMConfig:
    """LLM communication and context management settings."""

    llm_url: str = ""
    http_timeout: float = 30.0
    llm_max_retries: int = 3
    llm_retry_base_delay: float = 1.0
    llm_temperature: float = 0.2
    llm_max_tokens: int = 1024
    title_llm_temperature: float = 0.1
    title_llm_max_tokens: int = 20
    sse_heartbeat_timeout: float = 30.0
    sse_malformed_retry: int = 2
    sse_reconnect_max: int = 1
    llm_stream_retry_on_heartbeat_timeout: bool = True
    llm_stream_retry_on_malformed_chunk: bool = False
    tokenize_url: str = ""
    context_token_limit: int = 0
    context_char_limit: int = 8000
    context_compress_turns: int = 4
    history_protect_turns: int = 2
    budget_warn_ratio: float = 0.8

    def __post_init__(self) -> None:
        _v_llm_ccl(self)
        _v_llm_bwr(self)
        _v_llm_mr(self)
        _v_llm_rbd(self)
        _v_llm_temp(self)
        _v_llm_mt(self)
        _v_llm_shrt(self)
        _v_llm_smr(self)
        _v_llm_srm(self)


@dataclass
class RAGConfig:
    """RAG pipeline and vector search settings."""

    web_search_max_results: int = 5
    embed_url: str = ""
    use_semantic_cache: bool = False
    semantic_cache_threshold: float = 0.92
    semantic_cache_max_size: int = 100
    use_refiner: bool = False
    refiner_max_tokens: int = 512
    refiner_timeout: float = 30.0
    refiner_max_chars_per_chunk: int = 300

    def __post_init__(self) -> None:
        _v_rag_rmt(self)
        _v_rag_rt(self)
        _v_rag_rmcc(self)


@dataclass
class ToolConfig:
    """Tool execution, caching, approval policy, and prompt settings."""

    tool_cache_ttl: float = 300.0
    # LRU eviction when exceeded; 0 = unlimited
    tool_cache_max_size: int = 200
    # When True, tool calls execute one by one instead of asyncio.gather()
    serial_tool_calls: bool = False
    # Compare tool_definitions against /v1/tools at startup
    tool_definitions_strict: bool = False
    # Treat config/registry routing drift as fatal at startup; False = warn only
    routing_drift_strict: bool = False
    tool_dedup_max_repeats: int = 3
    # Window size for cyclic planning detection; 0 disables
    tool_cycle_detect_window: int = 2
    tool_error_max_consecutive: int = 3
    # Max retries for an (name, args) combo that returned an error; 0 = disabled
    tool_error_retry_max: int = 1
    # Per-server concurrent call limit; empty = unlimited
    tool_concurrency_limits: dict[str, int] = field(default_factory=dict)
    # Argument fields to redact in console output
    masked_fields: list[str] = field(default_factory=lambda: ["file_content"])
    # Tools blocked when plan_mode is active; empty = block nothing
    plan_blocked_tools: list[str] = field(
        default_factory=lambda: [
            "write_file",
            "create_directory",
            "delete_file",
            "delete_directory",
        ],
    )
    max_tool_turns: int = 5
    # Max chars of a tool result injected into LLM context
    tool_result_max_llm_chars: int = 8000
    # Max total chars of all tool results within one turn
    tool_results_turn_max_chars: int = 50000
    tool_definitions: list[dict] = field(default_factory=list)
    system_prompts: dict[str, str] = field(default_factory=dict)
    system_prompt_tool: str = ""
    # Empty = all tools allowed; non-empty = only listed tools allowed
    allowed_tools: list[str] = field(default_factory=list)
    # Tools that shadow MCP tool names are rejected by default.
    # true = allow shadowing with warning; false = reject (default)
    # Recommended for production: False (fail-closed)
    plugin_tool_override: bool = False
    # Fail startup on first plugin import error.
    # true = fail-fast (CI/production); false = fail-open (log and continue, dev)
    # Recommended for production: True
    plugin_strict: bool = False

    def __post_init__(self) -> None:
        _v_tool_dm(self)
        _v_tool_cdw(self)
        _v_tool_emc(self)
        _v_tool_cms(self)
        _v_tool_erm(self)
        _v_tool_pto(self)
        _v_tool_ps(self)


@dataclass
class MemoryConfig:
    """Persistent semantic memory layer settings."""

    use_memory_layer: bool = False
    memory_jsonl_dir: str = "/opt/llm/memory"
    memory_max_inject_semantic: int = 5
    memory_max_inject_episodic: int = 3
    memory_min_importance: float = 0.3
    # Enable embedding generation and KNN search
    memory_embed_enabled: bool = False
    # Dimension of embedding vectors; must match vec0 schema
    memory_embed_dim: int = 384
    # L2 distance threshold for deduplication
    memory_dedup_threshold: float = 0.3
    # Max chars per extracted memory entry
    memory_max_content_chars: int = 500
    # Timeout per embedding HTTP call
    memory_embed_timeout_sec: float = 5.0
    # Entries older than this are pruned
    memory_retention_days: int = 90
    # FTS5 candidate limit before rescoring
    memory_fts_limit: int = 50
    # RRF fusion constant
    memory_rrf_k: int = 60
    # Recency window in days for boost calculation
    memory_recency_days: float = 7.0
    # When true, reject non-local embed_url — local-only safety mode
    memory_local_only: bool = False

    def __post_init__(self) -> None:
        _v_mem_fts(self)
        _v_mem_rrf(self)
        _v_mem_rec(self)


@dataclass
class MCPConfig:
    """MCP server lifecycle and watchdog settings."""

    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)
    # Probe interval in seconds; 0 disables watchdog. Default 30s for production self-healing.
    mcp_watchdog_interval: float = 30.0
    mcp_watchdog_max_restarts: int = 3
    # Deployment security profile: "local" (auth optional) or "production" (auth required for HTTP).
    security_profile: SecurityProfile = SecurityProfile.LOCAL
    # Set to True to suppress deny-all startup warnings when deny-all is intentional.
    security_lockdown_enabled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.security_profile, SecurityProfile):
            self.security_profile = SecurityProfile(self.security_profile)


@dataclass
class ApprovalConfig:
    """Risk-based tool approval policy settings."""

    # tool_name -> "none" | "medium" | "high"; absent tools default to "medium" (fail-closed)
    approval_risk_rules: dict[str, str] = field(
        default_factory=lambda: {
            "write_file": "medium",
            "edit_file": "medium",
            "create_directory": "medium",
            "move_file": "medium",
            "delete_file": "high",
            "delete_directory": "high",
            "shell_run": "high",
            "github_push_files": "high",
            "github_create_or_update_file": "high",
            "github_delete_file": "high",
            "github_merge_pull_request": "high",
            "github_create_branch": "medium",
            "github_create_pull_request": "medium",
            "github_update_pull_request": "medium",
            "github_create_issue": "medium",
            "github_add_issue_comment": "medium",
        },
    )
    # File path prefixes that escalate any operation to "high" risk
    approval_protected_paths: list[str] = field(
        default_factory=lambda: [
            "/opt/",
            "/etc/",
            "/boot/",
            "/usr/",
            "/bin/",
            "/sbin/",
        ],
    )
    # GitHub branch names where write operations escalate to "high" risk
    approval_high_risk_branches: list[str] = field(
        default_factory=lambda: ["main", "master"],
    )
    # shell_run command prefixes always auto-approved despite "high" base level
    approval_shell_safe_prefixes: list[str] = field(
        default_factory=lambda: [
            "ls",
            "cat",
            "echo",
            "git log",
            "git status",
            "git diff",
            "git show",
            "git branch",
            "pwd",
            "find",
            "grep",
        ],
    )
    # Arg keys treated as resource identifiers for path/branch escalation
    approval_resource_keys: dict[str, list[str]] = field(
        default_factory=lambda: {
            "path_keys": [
                "path",
                "file_path",
                "directory_path",
                "source",
                "destination",
            ],
            "branch_keys": ["branch", "base", "head"],
        },
    )
    # Tools with dry_run=True support; approval flow injects dry_run automatically
    approval_dry_run_tools: list[str] = field(
        default_factory=lambda: [
            "write_file",
            "edit_file",
            "create_directory",
            "delete_file",
            "delete_directory",
            "move_file",
        ],
    )
    # tool_name -> "READ_ONLY" | "WRITE_SAFE" | "WRITE_DANGEROUS" | "ADMIN"
    # Absent tools default to "WRITE_DANGEROUS" (fail-safe)
    tool_safety_tiers: dict[str, str] = field(default_factory=dict)
    # Absolute path prefix all file paths must be relative to; "" disables
    allowed_root: str = ""
    # GitHub repos (owner/repo) allowed for write ops; empty = deny all (fail-closed)
    approval_github_allowed_repos: list[str] = field(default_factory=list)
    # Block all GitHub write operations globally when True
    gitops_push_blocked: bool = False
    # Block github_push_files with force=True
    gitops_force_push_blocked: bool = True
    # Protected branch names; push/merge to these requires high-risk approval
    gitops_protected_branches: list[str] = field(
        default_factory=lambda: ["main", "master"]
    )

    def __post_init__(self) -> None:
        _v_app_risk(self)
        _v_app_tier(self)


@dataclass
class ObservabilityConfig:
    """OpenTelemetry tracing, audit logging, and structured log settings."""

    otel_enabled: bool = False
    # OTLP HTTP endpoint; "" = ConsoleSpanExporter
    otel_endpoint: str = ""
    otel_service_name: str = "llm-agent"
    # Audit log receives turn-level JSON-lines events
    audit_log_file: str = "/opt/llm/logs/audit.log"
    # When True, agent.log uses JSON-lines format
    structured_log: bool = False


# ---------------------------------------------------------------------------
# Composite config
# ---------------------------------------------------------------------------


@dataclass
class AgentConfig:
    """Mutable runtime configuration shared by all agent components.

    Composes 7 domain-specific sub-configs.
    Access fields via nested paths: cfg.llm.llm_url, cfg.rag.use_semantic_cache, etc.
    security_lockdown_enabled: suppress DENY-ALL warnings for intentional lockdowns.
    """

    llm: LLMConfig = field(default_factory=LLMConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    tool: ToolConfig = field(default_factory=ToolConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    approval: ApprovalConfig = field(default_factory=ApprovalConfig)
    obs: ObservabilityConfig = field(default_factory=ObservabilityConfig)
    security_lockdown_enabled: bool = False

    def __post_init__(self) -> None:
        self._validate_cross_field()

    def _validate_cross_field(self) -> None:
        """Validate interdependent settings that span sub-config boundaries."""
        self._validate_semantic_cache_url()
        self._validate_memory_jsonl_dir()
        self._validate_memory_embed_url()

    def _validate_semantic_cache_url(self) -> None:
        if self.rag.use_semantic_cache and not self.rag.embed_url:
            raise ValueError(
                "use_semantic_cache=True requires embed_url to be non-empty",
            )

    def _validate_memory_jsonl_dir(self) -> None:
        if self.memory.use_memory_layer and not self.memory.memory_jsonl_dir:
            raise ValueError(
                "use_memory_layer=True requires memory_jsonl_dir to be non-empty",
            )

    def _validate_memory_embed_url(self) -> None:
        if self.memory.memory_embed_enabled and not self.rag.embed_url:
            raise ValueError(
                "memory_embed_enabled=True requires embed_url to be non-empty",
            )
