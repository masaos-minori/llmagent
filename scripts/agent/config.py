"""agent/config.py
Shared configuration dataclass and loader for the agent pipeline.

AgentConfig composes 7 domain-specific sub-configs.
Flat field access (e.g. cfg.llm_url) is preserved via __getattr__/__setattr__
for backward compatibility.  Full migration to cfg.llm.llm_url etc. follows
in a separate step.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from shared.config_loader import ConfigLoader
from shared.mcp_config import McpServerConfig, _build_mcp_servers

__all__ = ["AgentConfig", "ConfigLoadError", "McpServerConfig"]

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _SCRIPTS_DIR.parent / "config"


class ConfigLoadError(RuntimeError):
    """Raised when configuration files cannot be loaded."""


def load_config() -> dict[str, Any]:
    """Load configuration from files.  No module-level cache — always fresh."""
    try:
        return ConfigLoader().load_all()
    except Exception as e:
        raise ConfigLoadError(f"Config load failed: {e}") from e


# ---------------------------------------------------------------------------
# Sub-config dataclasses
# ---------------------------------------------------------------------------


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
        if self.context_char_limit < 0:
            raise ValueError(
                f"context_char_limit must be >= 0, got {self.context_char_limit}",
            )
        if not 0.0 < self.budget_warn_ratio <= 1.0:
            raise ValueError(
                f"budget_warn_ratio must be in (0.0, 1.0], got {self.budget_warn_ratio}",
            )
        if self.llm_max_retries < 0:
            raise ValueError(
                f"llm_max_retries must be >= 0, got {self.llm_max_retries}",
            )
        if self.llm_retry_base_delay <= 0:
            raise ValueError(
                f"llm_retry_base_delay must be > 0, got {self.llm_retry_base_delay}",
            )
        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError(
                f"llm_temperature must be in [0.0, 2.0], got {self.llm_temperature}",
            )
        if self.llm_max_tokens < 1:
            raise ValueError(f"llm_max_tokens must be >= 1, got {self.llm_max_tokens}")
        if self.sse_heartbeat_timeout < 0:
            raise ValueError(
                f"sse_heartbeat_timeout must be >= 0, got {self.sse_heartbeat_timeout}",
            )
        if self.sse_malformed_retry < 0:
            raise ValueError(
                f"sse_malformed_retry must be >= 0, got {self.sse_malformed_retry}",
            )
        if self.sse_reconnect_max < 0:
            raise ValueError(
                f"sse_reconnect_max must be >= 0, got {self.sse_reconnect_max}",
            )


@dataclass
class RAGConfig:
    """RAG pipeline and vector search settings."""

    top_k_search: int = 20
    top_k_rerank: int = 15
    max_chunks_per_doc: int = 2
    web_search_url: str = ""
    web_search_max_results: int = 5
    embed_url: str = "http://127.0.0.1:8003/embedding"
    use_semantic_cache: bool = False
    semantic_cache_threshold: float = 0.92
    semantic_cache_max_size: int = 100
    use_refiner: bool = False
    refiner_max_tokens: int = 512
    refiner_timeout: float = 30.0
    refiner_max_chars_per_chunk: int = 300

    def __post_init__(self) -> None:
        if self.top_k_search < 1:
            raise ValueError(f"top_k_search must be >= 1, got {self.top_k_search}")
        if self.top_k_rerank < 1:
            raise ValueError(f"top_k_rerank must be >= 1, got {self.top_k_rerank}")
        if self.max_chunks_per_doc < 1:
            raise ValueError(
                f"max_chunks_per_doc must be >= 1, got {self.max_chunks_per_doc}",
            )
        if self.refiner_max_tokens < 1:
            raise ValueError(
                f"refiner_max_tokens must be >= 1, got {self.refiner_max_tokens}",
            )
        if self.refiner_timeout <= 0:
            raise ValueError(f"refiner_timeout must be > 0, got {self.refiner_timeout}")
        if self.refiner_max_chars_per_chunk < 1:
            raise ValueError(
                f"refiner_max_chars_per_chunk must be >= 1,"
                f" got {self.refiner_max_chars_per_chunk}",
            )


@dataclass
class ToolConfig:
    """Tool execution, caching, approval policy, and prompt settings."""

    tool_cache_ttl: float = 300.0
    # LRU eviction when exceeded; 0 = unlimited
    tool_cache_max_size: int = 200
    # When True, tool calls execute one by one instead of asyncio.gather()
    serial_tool_calls: bool = False
    # Append all notes-table entries to system prompt at startup
    auto_inject_notes: bool = True
    # Replace truncation with LLM summary above threshold
    use_tool_summarize: bool = False
    tool_summarize_threshold: int = 3000
    # Compare tool_definitions against /v1/tools at startup
    tool_definitions_strict: bool = False
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
    # Place WRITE_TOOLS before READ_TOOLS/others within the same turn
    use_tool_dag: bool = False
    tool_definitions: list[dict] = field(default_factory=list)
    system_prompts: dict[str, str] = field(default_factory=dict)
    system_prompt_tool: str = ""
    # Empty = all tools allowed; non-empty = only listed tools allowed
    allowed_tools: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.tool_dedup_max_repeats < 1:
            raise ValueError(
                f"tool_dedup_max_repeats must be >= 1, got {self.tool_dedup_max_repeats}",
            )
        if self.tool_cycle_detect_window < 0:
            raise ValueError(
                "tool_cycle_detect_window must be >= 0,"
                f" got {self.tool_cycle_detect_window}",
            )
        if self.tool_error_max_consecutive < 0:
            raise ValueError(
                "tool_error_max_consecutive must be >= 0,"
                f" got {self.tool_error_max_consecutive}",
            )
        if self.tool_cache_max_size < 0:
            raise ValueError(
                f"tool_cache_max_size must be >= 0, got {self.tool_cache_max_size}",
            )
        if self.tool_error_retry_max < 0:
            raise ValueError(
                f"tool_error_retry_max must be >= 0, got {self.tool_error_retry_max}",
            )


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


@dataclass
class MCPConfig:
    """MCP server lifecycle and watchdog settings."""

    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)
    # Probe interval in seconds; 0 disables watchdog
    mcp_watchdog_interval: float = 0.0
    mcp_watchdog_max_restarts: int = 3
    github_url: str = "http://127.0.0.1:8006"


@dataclass
class ApprovalConfig:
    """Risk-based tool approval policy settings."""

    # tool_name → "none" | "medium" | "high"; absent tools default to "medium" (fail-closed)
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
            "delete_file",
            "delete_directory",
            "move_file",
        ],
    )
    # tool_name → "READ_ONLY" | "WRITE_SAFE" | "WRITE_DANGEROUS" | "ADMIN"
    # Absent tools default to "WRITE_DANGEROUS" (fail-safe)
    tool_safety_tiers: dict[str, str] = field(default_factory=dict)
    # Absolute path prefix all file paths must be relative to; "" disables
    allowed_root: str = ""
    # GitHub repos (owner/repo) allowed for write ops; empty = deny all (fail-closed)
    approval_github_allowed_repos: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        _valid_risk = {"none", "medium", "high"}
        bad = {
            k: v for k, v in self.approval_risk_rules.items() if v not in _valid_risk
        }
        if bad:
            raise ValueError(
                f"approval_risk_rules: invalid levels {bad};"
                " must be 'none', 'medium', or 'high'",
            )
        _valid_tiers = {"READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"}
        bad_tiers = {
            k: v for k, v in self.tool_safety_tiers.items() if v not in _valid_tiers
        }
        if bad_tiers:
            raise ValueError(
                f"tool_safety_tiers: invalid tier values {bad_tiers};"
                " must be READ_ONLY, WRITE_SAFE, WRITE_DANGEROUS, or ADMIN",
            )


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
# Composite config with backward-compat flat attribute access
# ---------------------------------------------------------------------------


@dataclass
class AgentConfig:
    """Mutable runtime configuration shared by all agent components.

    Composes 7 domain-specific sub-configs.  Flat attribute access such as
    ``cfg.llm_url`` is preserved via ``__getattr__`` / ``__setattr__`` for
    backward compatibility with existing code.
    """

    llm: LLMConfig = field(default_factory=LLMConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    tool: ToolConfig = field(default_factory=ToolConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    approval: ApprovalConfig = field(default_factory=ApprovalConfig)
    obs: ObservabilityConfig = field(default_factory=ObservabilityConfig)

    def __post_init__(self) -> None:
        self._validate_cross_field()

    def _validate_cross_field(self) -> None:
        """Validate interdependent settings that span sub-config boundaries."""
        if self.rag.use_semantic_cache and not self.rag.embed_url:
            raise ValueError(
                "use_semantic_cache=True requires embed_url to be non-empty",
            )
        if self.memory.use_memory_layer and not self.memory.memory_jsonl_dir:
            raise ValueError(
                "use_memory_layer=True requires memory_jsonl_dir to be non-empty",
            )
        if self.memory.memory_embed_enabled and not self.rag.embed_url:
            raise ValueError(
                "memory_embed_enabled=True requires embed_url to be non-empty",
            )


# ---------------------------------------------------------------------------
# Config construction helpers
# ---------------------------------------------------------------------------

_DEFAULT_PLAN_BLOCKED_TOOLS: list[str] = [
    "write_file",
    "create_directory",
    "delete_file",
    "delete_directory",
]
_DEFAULT_APPROVAL_RISK_RULES: dict[str, str] = {
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
}
_DEFAULT_PROTECTED_PATHS: list[str] = [
    "/opt/",
    "/etc/",
    "/boot/",
    "/usr/",
    "/bin/",
    "/sbin/",
]
_DEFAULT_SHELL_SAFE_PREFIXES: list[str] = [
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
]
_DEFAULT_RESOURCE_KEYS: dict[str, list[str]] = {
    "path_keys": ["path", "file_path", "directory_path", "source", "destination"],
    "branch_keys": ["branch", "base", "head"],
}
_DEFAULT_DRY_RUN_TOOLS: list[str] = [
    "write_file",
    "edit_file",
    "delete_file",
    "delete_directory",
    "move_file",
]


def _build_llm_config(cfg: dict[str, Any]) -> "LLMConfig":
    return LLMConfig(
        llm_url=cfg.get("llm_url", ""),
        http_timeout=float(cfg.get("http_timeout", 30.0)),
        llm_max_retries=int(cfg.get("llm_max_retries", 3)),
        llm_retry_base_delay=float(cfg.get("llm_retry_base_delay", 1.0)),
        llm_temperature=float(cfg.get("llm_temperature", 0.2)),
        llm_max_tokens=int(cfg.get("llm_max_tokens", 1024)),
        title_llm_temperature=float(cfg.get("title_llm_temperature", 0.1)),
        title_llm_max_tokens=int(cfg.get("title_llm_max_tokens", 20)),
        sse_heartbeat_timeout=float(cfg.get("sse_heartbeat_timeout", 30.0)),
        sse_malformed_retry=int(cfg.get("sse_malformed_retry", 2)),
        sse_reconnect_max=int(cfg.get("sse_reconnect_max", 1)),
        llm_stream_retry_on_heartbeat_timeout=bool(
            cfg.get("llm_stream_retry_on_heartbeat_timeout", True),
        ),
        llm_stream_retry_on_malformed_chunk=bool(
            cfg.get("llm_stream_retry_on_malformed_chunk", False),
        ),
        tokenize_url=str(cfg.get("tokenize_url", "")),
        context_token_limit=int(cfg.get("context_token_limit", 0)),
        context_char_limit=int(cfg.get("context_char_limit", 8000)),
        context_compress_turns=int(cfg.get("context_compress_turns", 4)),
        history_protect_turns=int(cfg.get("history_protect_turns", 2)),
        budget_warn_ratio=float(cfg.get("budget_warn_ratio", 0.8)),
    )


def _build_rag_config(cfg: dict[str, Any]) -> "RAGConfig":
    return RAGConfig(
        top_k_search=int(cfg.get("top_k_search", 20)),
        top_k_rerank=int(cfg.get("top_k_rerank", 15)),
        max_chunks_per_doc=int(cfg.get("max_chunks_per_doc", 2)),
        web_search_url=cfg.get("web_search_url", ""),
        web_search_max_results=int(cfg.get("web_search_max_results", 5)),
        embed_url=cfg.get("embed_url", "http://127.0.0.1:8003/embedding"),
        use_semantic_cache=bool(cfg.get("use_semantic_cache", False)),
        semantic_cache_threshold=float(cfg.get("semantic_cache_threshold", 0.92)),
        semantic_cache_max_size=int(cfg.get("semantic_cache_max_size", 100)),
        use_refiner=bool(cfg.get("use_refiner", False)),
        refiner_max_tokens=int(cfg.get("refiner_max_tokens", 512)),
        refiner_timeout=float(cfg.get("refiner_timeout", 30.0)),
        refiner_max_chars_per_chunk=int(cfg.get("refiner_max_chars_per_chunk", 300)),
    )


def _build_tool_config(cfg: dict[str, Any], system_prompt_tool: str) -> "ToolConfig":
    return ToolConfig(
        tool_cache_ttl=float(cfg.get("tool_cache_ttl", 300)),
        tool_cache_max_size=int(cfg.get("tool_cache_max_size", 200)),
        serial_tool_calls=bool(cfg.get("serial_tool_calls", False)),
        auto_inject_notes=bool(cfg.get("auto_inject_notes", True)),
        use_tool_summarize=bool(cfg.get("use_tool_summarize", False)),
        tool_summarize_threshold=int(cfg.get("tool_summarize_threshold", 3000)),
        tool_definitions_strict=bool(cfg.get("tool_definitions_strict", False)),
        tool_dedup_max_repeats=int(cfg.get("tool_dedup_max_repeats", 3)),
        tool_cycle_detect_window=int(cfg.get("tool_cycle_detect_window", 2)),
        tool_error_max_consecutive=int(cfg.get("tool_error_max_consecutive", 3)),
        tool_error_retry_max=int(cfg.get("tool_error_retry_max", 1)),
        tool_concurrency_limits=dict(cfg.get("tool_concurrency_limits", {})),
        masked_fields=list(cfg.get("masked_fields", ["file_content"])),
        plan_blocked_tools=list(
            cfg.get("plan_blocked_tools", _DEFAULT_PLAN_BLOCKED_TOOLS),
        ),
        max_tool_turns=int(cfg.get("max_tool_turns", 5)),
        tool_result_max_llm_chars=int(cfg.get("tool_result_max_llm_chars", 8000)),
        tool_results_turn_max_chars=int(cfg.get("tool_results_turn_max_chars", 50000)),
        use_tool_dag=bool(cfg.get("use_tool_dag", False)),
        tool_definitions=list(cfg.get("tool_definitions", [])),
        system_prompts=dict(
            cfg.get("system_prompts", {"default": system_prompt_tool}),
        ),
        system_prompt_tool=system_prompt_tool,
        allowed_tools=list(cfg.get("allowed_tools", [])),
    )


def _build_memory_config(cfg: dict[str, Any]) -> "MemoryConfig":
    return MemoryConfig(
        use_memory_layer=bool(cfg.get("use_memory_layer", False)),
        memory_jsonl_dir=str(cfg.get("memory_jsonl_dir", "/opt/llm/memory")),
        memory_max_inject_semantic=int(cfg.get("memory_max_inject_semantic", 5)),
        memory_max_inject_episodic=int(cfg.get("memory_max_inject_episodic", 3)),
        memory_min_importance=float(cfg.get("memory_min_importance", 0.3)),
        memory_embed_enabled=bool(cfg.get("memory_embed_enabled", False)),
        memory_embed_dim=int(cfg.get("memory_embed_dim", 384)),
        memory_dedup_threshold=float(cfg.get("memory_dedup_threshold", 0.3)),
        memory_max_content_chars=int(cfg.get("memory_max_content_chars", 500)),
        memory_embed_timeout_sec=float(cfg.get("memory_embed_timeout_sec", 5.0)),
        memory_retention_days=int(cfg.get("memory_retention_days", 90)),
    )


def _build_approval_config(cfg: dict[str, Any]) -> "ApprovalConfig":
    return ApprovalConfig(
        approval_risk_rules=dict(
            cfg.get("approval_risk_rules", _DEFAULT_APPROVAL_RISK_RULES),
        ),
        approval_protected_paths=list(
            cfg.get("approval_protected_paths", _DEFAULT_PROTECTED_PATHS),
        ),
        approval_high_risk_branches=list(
            cfg.get("approval_high_risk_branches", ["main", "master"]),
        ),
        approval_shell_safe_prefixes=list(
            cfg.get("approval_shell_safe_prefixes", _DEFAULT_SHELL_SAFE_PREFIXES),
        ),
        approval_resource_keys=dict(
            cfg.get("approval_resource_keys", _DEFAULT_RESOURCE_KEYS),
        ),
        approval_dry_run_tools=list(
            cfg.get("approval_dry_run_tools", _DEFAULT_DRY_RUN_TOOLS),
        ),
        tool_safety_tiers=dict(cfg.get("tool_safety_tiers", {})),
        allowed_root=cfg.get("allowed_root", ""),
        approval_github_allowed_repos=list(
            cfg.get("approval_github_allowed_repos", []),
        ),
    )


def build_agent_config(cfg_override: dict[str, Any] | None = None) -> "AgentConfig":
    """Construct AgentConfig from a config dict.

    If cfg_override is provided it is used directly (for /reload and tests).
    Otherwise configuration is loaded from files via load_config().
    """
    cfg = cfg_override if cfg_override is not None else load_config()
    system_prompt_tool = cfg.get("system_prompt_tool", "")
    return AgentConfig(
        llm=_build_llm_config(cfg),
        rag=_build_rag_config(cfg),
        tool=_build_tool_config(cfg, system_prompt_tool),
        memory=_build_memory_config(cfg),
        mcp=MCPConfig(
            mcp_servers=_build_mcp_servers(cfg),
            mcp_watchdog_interval=float(cfg.get("mcp_watchdog_interval", 0.0)),
            mcp_watchdog_max_restarts=int(cfg.get("mcp_watchdog_max_restarts", 3)),
            github_url=cfg.get("github_server_url", "http://127.0.0.1:8006"),
        ),
        approval=_build_approval_config(cfg),
        obs=ObservabilityConfig(
            otel_enabled=bool(cfg.get("otel_enabled", False)),
            otel_endpoint=cfg.get("otel_endpoint", ""),
            otel_service_name=cfg.get("otel_service_name", "llm-agent"),
            audit_log_file=cfg.get("audit_log_file", "/opt/llm/logs/audit.log"),
            structured_log=bool(cfg.get("structured_log", False)),
        ),
    )


@dataclass
class DbConfig:
    """Immutable configuration for the SQLite database and embedding service."""

    rag_db_path: str
    session_db_path: str
    sqlite_vec_so: str
    embed_url: str
    sqlite_timeout: int = 30

    def __post_init__(self) -> None:
        if not self.rag_db_path:
            raise ValueError("rag_db_path must not be empty")
        if not self.session_db_path:
            raise ValueError("session_db_path must not be empty")
        if not self.sqlite_vec_so:
            raise ValueError("sqlite_vec_so must not be empty")
        if not self.embed_url:
            raise ValueError("embed_url must not be empty")
        if self.sqlite_timeout < 1:
            raise ValueError(f"sqlite_timeout must be >= 1, got {self.sqlite_timeout}")


def build_db_config() -> "DbConfig":
    """Construct DbConfig from common.toml configuration via load_config()."""
    cfg = load_config()
    return DbConfig(
        rag_db_path=cfg.get("rag_db_path", ""),
        session_db_path=cfg.get("session_db_path", ""),
        sqlite_vec_so=cfg.get("sqlite_vec_so", ""),
        embed_url=cfg.get("embed_url", ""),
        sqlite_timeout=int(cfg.get("sqlite_timeout", 30)),
    )
