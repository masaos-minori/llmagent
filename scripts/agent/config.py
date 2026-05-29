#!/usr/bin/env python3
"""
agent_config.py
Shared configuration dataclass and loader for the agent pipeline.
All runtime-configurable values live in AgentConfig (hot-reloadable via /reload).
Only path constants remain at module level.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from shared.config_loader import ConfigLoader
from shared.mcp_config import McpServerConfig, _build_mcp_servers

__all__ = ["McpServerConfig", "AgentConfig"]

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("common.toml", "agent.toml")
        except Exception as e:
            logging.getLogger(__name__).warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
_CONFIG_DIR = _SCRIPTS_DIR.parent / "config"


@dataclass
class AgentConfig:
    """Mutable runtime configuration shared by all agent components."""

    context_char_limit: int
    context_compress_turns: int
    tool_cache_ttl: float
    top_k_search: int
    top_k_rerank: int
    rag_top_k: int
    use_mqe: bool
    use_search: bool
    use_rrf: bool
    use_rerank: bool
    llm_max_retries: int
    llm_retry_base_delay: float
    # Rerank score threshold: chunks scoring below this value are discarded (0–10 scale)
    rag_min_score: float
    # Max chunks per document to include after dedup; prevents near-duplicate flooding
    max_chunks_per_doc: int
    # Two-stage fetch: expand to full document when LLM signals insufficient context
    use_two_stage_fetch: bool
    two_stage_max_docs: int
    # When True, tool calls are executed one by one instead of asyncio.gather()
    serial_tool_calls: bool
    # When True, all notes from the notes table are appended to the system prompt
    # at startup
    auto_inject_notes: bool
    # Tool result summarization: replace truncation with LLM summary above threshold
    use_tool_summarize: bool
    tool_summarize_threshold: int
    # Semantic cache: reuse RAG context for queries with cosine similarity >= threshold
    use_semantic_cache: bool
    semantic_cache_threshold: float
    semantic_cache_max_size: int
    # Startup check: compare agent.toml tool_definitions against /v1/tools from
    # each MCP server
    tool_definitions_strict: bool
    # MCP watchdog: probe interval in seconds; 0 disables
    mcp_watchdog_interval: float
    mcp_watchdog_max_restarts: int
    # Argument fields to redact in console output (e.g. "file_content")
    masked_fields: list[str]
    # Tools blocked when plan_mode is active; empty list means block nothing
    plan_blocked_tools: list[str]
    # LLM generation parameters for the main conversation turn (hot-reloadable)
    llm_temperature: float
    llm_max_tokens: int
    # RAG context Refiner: compress chunks to query-relevant key points before injection
    use_refiner: bool
    refiner_max_tokens: int
    refiner_timeout: float
    refiner_max_chars_per_chunk: int
    # Tool loop guards: detect repeated calls, cyclic rounds, and consecutive all-error turns
    tool_dedup_max_repeats: int
    # Window size for cyclic planning detection (round-level fingerprint repetition); 0 disables
    tool_cycle_detect_window: int
    tool_error_max_consecutive: int
    # Max size of the TTL tool result cache; LRU eviction when exceeded. 0 = unlimited.
    tool_cache_max_size: int = 200
    # Max retries for an (name, args) combo that already returned an error this turn; 0 = disabled.
    tool_error_retry_max: int = 1
    # Per-server concurrent call limit for asyncio.gather; empty = unlimited.
    # Keys match _route() server keys: file_read, file_write, file_delete, shell, web_search, github.
    # Unknown keys produce a logger.warning in ToolExecutor.__init__ and are silently ignored.
    tool_concurrency_limits: dict[str, int] = field(default_factory=dict)
    # Per-server transport configuration (keyed by server role: "file", "github", "web_search")
    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)

    # Optional URL for external RAG HTTP service (port 8010); empty = in-process
    rag_service_url: str = ""

    # ── URL / HTTP config (hot-reloadable via /reload) ─────────────────────────
    llm_url: str = ""
    github_url: str = "http://127.0.0.1:8006"
    web_search_url: str = ""
    embed_url: str = "http://127.0.0.1:8003/embedding"
    http_timeout: float = 30.0
    web_search_max_results: int = 5

    # ── Tool / prompt config (hot-reloadable via /reload) ──────────────────────
    # Tool definitions loaded from agent.toml; reloaded via /reload
    tool_definitions: list[dict] = field(default_factory=list)
    # Named system prompt presets for /system command (agent.toml system_prompts)
    system_prompts: dict[str, str] = field(default_factory=dict)
    system_prompt_tool: str = ""
    max_tool_turns: int = 5
    # Max characters of a tool result injected into LLM context; truncates beyond this
    tool_result_max_llm_chars: int = 8000
    # Max total chars of all tool results injected into the LLM history within one turn;
    # results exceeding this budget are replaced with a retrieval hint for /tool show
    tool_results_turn_max_chars: int = 50000

    # Phase 1: history compression safety + memory layer
    # Token-based monitoring threshold for history compression (0 = disabled)
    context_token_limit: int = 0
    # Number of most-recent turns to protect from compression
    history_protect_turns: int = 2
    # Enable Long-term/Semantic/Task memory layer
    use_memory_layer: bool = False
    # Phase 2: OpenTelemetry observability
    # Enable OpenTelemetry span collection
    otel_enabled: bool = False
    # OTLP HTTP endpoint; empty string = ConsoleSpanExporter
    otel_endpoint: str = ""
    # OTel service.name reported in spans
    otel_service_name: str = "llm-agent"
    # Audit log file path; receives turn-level JSON-lines events
    audit_log_file: str = "/opt/llm/logs/audit.log"
    # When True, agent.log uses JSON-lines format instead of plain text
    structured_log: bool = False
    # Fraction of context_char_limit / context_token_limit that triggers a budget warning
    budget_warn_ratio: float = 0.8
    # Risk-based approval: tool_name → "none" | "medium" | "high"
    # Tools absent from this dict are auto-approved (treated as "none").
    approval_risk_rules: dict[str, str] = field(default_factory=dict)
    # File path prefixes that escalate any operation to "high" risk
    approval_protected_paths: list[str] = field(default_factory=list)
    # GitHub branch names where write operations escalate to "high" risk
    approval_high_risk_branches: list[str] = field(default_factory=list)
    # shell_run command prefixes that are always auto-approved despite "high" base level
    approval_shell_safe_prefixes: list[str] = field(default_factory=list)
    # Arg keys treated as resource identifiers for path/branch escalation and audit scope
    # Keys: "path_keys" (file paths), "branch_keys" (git branch names)
    approval_resource_keys: dict[str, list[str]] = field(default_factory=dict)
    # Tools that support dry_run=True; approval flow executes dry_run before prompting
    approval_dry_run_tools: list[str] = field(default_factory=list)
    # Tool safety tier: tool_name → "READ_ONLY" | "WRITE_SAFE" | "WRITE_DANGEROUS" | "ADMIN"
    # Absent tools fall back to "WRITE_DANGEROUS" (Fail-Safe).
    # approval_risk_rules always takes priority over tier-derived defaults.
    tool_safety_tiers: dict[str, str] = field(default_factory=dict)
    # Absolute path prefix that all file path arguments must be relative to.
    # Empty string disables the root jail check.
    allowed_root: str = ""
    # GitHub repos (owner/repo) allowed for write operations.
    # Empty list = Fail-Closed: all write ops to any repo are denied.
    approval_github_allowed_repos: list[str] = field(default_factory=list)
    # Seconds of SSE inactivity before HEARTBEAT_TIMEOUT is raised (0 = disabled)
    sse_heartbeat_timeout: float = 30.0
    # Number of malformed SSE frames to tolerate before raising MALFORMED_SSE_FRAME
    sse_malformed_retry: int = 2
    # Maximum SSE reconnect attempts on retryable in-stream errors (0 = no reconnect)
    sse_reconnect_max: int = 1
    # When True, HEARTBEAT_TIMEOUT triggers a reconnect attempt if no partial output
    llm_stream_retry_on_heartbeat_timeout: bool = True
    # When True, MALFORMED_SSE_FRAME (after budget exhausted) triggers a reconnect
    llm_stream_retry_on_malformed_chunk: bool = False

    def __post_init__(self) -> None:
        self._validate_llm_params()
        self._validate_rag_params()
        self._validate_tool_params()

    def _validate_llm_params(self) -> None:
        if self.context_char_limit < 0:
            raise ValueError(
                f"context_char_limit must be >= 0, got {self.context_char_limit}"
            )
        if not 0.0 < self.budget_warn_ratio <= 1.0:
            raise ValueError(
                f"budget_warn_ratio must be in (0.0, 1.0], got {self.budget_warn_ratio}"
            )
        if self.llm_max_retries < 0:
            raise ValueError(
                f"llm_max_retries must be >= 0, got {self.llm_max_retries}"
            )
        if self.llm_retry_base_delay <= 0:
            raise ValueError(
                f"llm_retry_base_delay must be > 0, got {self.llm_retry_base_delay}"
            )
        if not 0.0 <= self.llm_temperature <= 2.0:
            raise ValueError(
                f"llm_temperature must be in [0.0, 2.0], got {self.llm_temperature}"
            )
        if self.llm_max_tokens < 1:
            raise ValueError(f"llm_max_tokens must be >= 1, got {self.llm_max_tokens}")
        if self.sse_heartbeat_timeout < 0:
            raise ValueError(
                f"sse_heartbeat_timeout must be >= 0, got {self.sse_heartbeat_timeout}"
            )
        if self.sse_malformed_retry < 0:
            raise ValueError(
                f"sse_malformed_retry must be >= 0, got {self.sse_malformed_retry}"
            )
        if self.sse_reconnect_max < 0:
            raise ValueError(
                f"sse_reconnect_max must be >= 0, got {self.sse_reconnect_max}"
            )

    def _validate_rag_params(self) -> None:
        if self.top_k_search < 1:
            raise ValueError(f"top_k_search must be >= 1, got {self.top_k_search}")
        if self.top_k_rerank < 1:
            raise ValueError(f"top_k_rerank must be >= 1, got {self.top_k_rerank}")
        if self.rag_top_k < 1:
            raise ValueError(f"rag_top_k must be >= 1, got {self.rag_top_k}")
        if self.rag_min_score < 0.0:
            raise ValueError(f"rag_min_score must be >= 0, got {self.rag_min_score}")
        if self.max_chunks_per_doc < 1:
            raise ValueError(
                f"max_chunks_per_doc must be >= 1, got {self.max_chunks_per_doc}"
            )
        if self.two_stage_max_docs < 1:
            raise ValueError(
                f"two_stage_max_docs must be >= 1, got {self.two_stage_max_docs}"
            )
        if self.refiner_max_tokens < 1:
            raise ValueError(
                f"refiner_max_tokens must be >= 1, got {self.refiner_max_tokens}"
            )
        if self.refiner_timeout <= 0:
            raise ValueError(f"refiner_timeout must be > 0, got {self.refiner_timeout}")
        if self.refiner_max_chars_per_chunk < 1:
            raise ValueError(
                f"refiner_max_chars_per_chunk must be >= 1,"
                f" got {self.refiner_max_chars_per_chunk}"
            )

    def _validate_tool_params(self) -> None:
        _valid_risk = {"none", "medium", "high"}
        bad = {
            k: v for k, v in self.approval_risk_rules.items() if v not in _valid_risk
        }
        if bad:
            raise ValueError(
                f"approval_risk_rules: invalid levels {bad};"
                " must be 'none', 'medium', or 'high'"
            )
        _valid_tiers = {"READ_ONLY", "WRITE_SAFE", "WRITE_DANGEROUS", "ADMIN"}
        bad_tiers = {
            k: v for k, v in self.tool_safety_tiers.items() if v not in _valid_tiers
        }
        if bad_tiers:
            raise ValueError(
                f"tool_safety_tiers: invalid tier values {bad_tiers};"
                " must be READ_ONLY, WRITE_SAFE, WRITE_DANGEROUS, or ADMIN"
            )
        if self.tool_dedup_max_repeats < 1:
            raise ValueError(
                f"tool_dedup_max_repeats must be >= 1, got {self.tool_dedup_max_repeats}"
            )
        if self.tool_cycle_detect_window < 0:
            raise ValueError(
                "tool_cycle_detect_window must be >= 0,"
                f" got {self.tool_cycle_detect_window}"
            )
        if self.tool_error_max_consecutive < 0:
            raise ValueError(
                "tool_error_max_consecutive must be >= 0,"
                f" got {self.tool_error_max_consecutive}"
            )
        if self.tool_cache_max_size < 0:
            raise ValueError(
                f"tool_cache_max_size must be >= 0, got {self.tool_cache_max_size}"
            )
        if self.tool_error_retry_max < 0:
            raise ValueError(
                f"tool_error_retry_max must be >= 0, got {self.tool_error_retry_max}"
            )


def build_agent_config(cfg_override: dict | None = None) -> "AgentConfig":
    """Construct AgentConfig from config dict.

    If cfg_override is provided, uses it directly (for /reload and tests).
    Otherwise loads from config files via _get_cfg().
    """
    cfg = cfg_override if cfg_override is not None else _get_cfg()
    system_prompt_tool = cfg.get("system_prompt_tool", "")
    return AgentConfig(
        context_char_limit=cfg.get("context_char_limit", 8000),
        context_compress_turns=cfg.get("context_compress_turns", 4),
        tool_cache_ttl=cfg.get("tool_cache_ttl", 300),
        top_k_search=cfg.get("top_k_search", 20),
        top_k_rerank=cfg.get("top_k_rerank", 15),
        rag_top_k=int(cfg.get("rag_top_k", 5)),
        use_mqe=cfg.get("use_mqe", True),
        use_search=cfg.get("use_search", True),
        use_rrf=cfg.get("use_rrf", True),
        use_rerank=cfg.get("use_rerank", True),
        llm_max_retries=int(cfg.get("llm_max_retries", 3)),
        llm_retry_base_delay=float(cfg.get("llm_retry_base_delay", 1.0)),
        rag_min_score=float(cfg.get("rag_min_score", 0.0)),
        max_chunks_per_doc=int(cfg.get("max_chunks_per_doc", 2)),
        use_two_stage_fetch=bool(cfg.get("use_two_stage_fetch", False)),
        two_stage_max_docs=int(cfg.get("two_stage_max_docs", 2)),
        serial_tool_calls=bool(cfg.get("serial_tool_calls", False)),
        auto_inject_notes=bool(cfg.get("auto_inject_notes", True)),
        use_tool_summarize=bool(cfg.get("use_tool_summarize", False)),
        tool_summarize_threshold=int(cfg.get("tool_summarize_threshold", 3000)),
        use_semantic_cache=bool(cfg.get("use_semantic_cache", False)),
        semantic_cache_threshold=float(cfg.get("semantic_cache_threshold", 0.92)),
        semantic_cache_max_size=int(cfg.get("semantic_cache_max_size", 100)),
        tool_definitions_strict=bool(cfg.get("tool_definitions_strict", False)),
        mcp_watchdog_interval=float(cfg.get("mcp_watchdog_interval", 0.0)),
        mcp_watchdog_max_restarts=int(cfg.get("mcp_watchdog_max_restarts", 3)),
        masked_fields=list(cfg.get("masked_fields", ["file_content"])),
        plan_blocked_tools=list(
            cfg.get(
                "plan_blocked_tools",
                ["write_file", "create_directory", "delete_file", "delete_directory"],
            )
        ),
        llm_temperature=float(cfg.get("llm_temperature", 0.2)),
        llm_max_tokens=int(cfg.get("llm_max_tokens", 1024)),
        use_refiner=bool(cfg.get("use_refiner", False)),
        refiner_max_tokens=int(cfg.get("refiner_max_tokens", 512)),
        refiner_timeout=float(cfg.get("refiner_timeout", 30.0)),
        refiner_max_chars_per_chunk=int(cfg.get("refiner_max_chars_per_chunk", 300)),
        tool_dedup_max_repeats=int(cfg.get("tool_dedup_max_repeats", 3)),
        tool_cycle_detect_window=int(cfg.get("tool_cycle_detect_window", 2)),
        tool_error_max_consecutive=int(cfg.get("tool_error_max_consecutive", 3)),
        tool_cache_max_size=int(cfg.get("tool_cache_max_size", 200)),
        tool_error_retry_max=int(cfg.get("tool_error_retry_max", 1)),
        tool_concurrency_limits=dict(cfg.get("tool_concurrency_limits", {})),
        rag_service_url=cfg.get("rag_service_url", ""),
        mcp_servers=_build_mcp_servers(cfg),
        llm_url=cfg.get("llm_url", ""),
        github_url=cfg.get("github_server_url", "http://127.0.0.1:8006"),
        web_search_url=cfg.get("web_search_url", ""),
        embed_url=cfg.get("embed_url", "http://127.0.0.1:8003/embedding"),
        http_timeout=float(cfg.get("http_timeout", 30.0)),
        web_search_max_results=int(cfg.get("web_search_max_results", 5)),
        tool_definitions=list(cfg.get("tool_definitions", [])),
        system_prompts=dict(cfg.get("system_prompts", {"default": system_prompt_tool})),
        system_prompt_tool=system_prompt_tool,
        max_tool_turns=int(cfg.get("max_tool_turns", 5)),
        tool_result_max_llm_chars=int(cfg.get("tool_result_max_llm_chars", 8000)),
        tool_results_turn_max_chars=int(cfg.get("tool_results_turn_max_chars", 50000)),
        context_token_limit=int(cfg.get("context_token_limit", 0)),
        history_protect_turns=int(cfg.get("history_protect_turns", 2)),
        use_memory_layer=bool(cfg.get("use_memory_layer", False)),
        otel_enabled=bool(cfg.get("otel_enabled", False)),
        otel_endpoint=cfg.get("otel_endpoint", ""),
        otel_service_name=cfg.get("otel_service_name", "llm-agent"),
        audit_log_file=cfg.get("audit_log_file", "/opt/llm/logs/audit.log"),
        structured_log=bool(cfg.get("structured_log", False)),
        budget_warn_ratio=float(cfg.get("budget_warn_ratio", 0.8)),
        approval_risk_rules=dict(
            cfg.get(
                "approval_risk_rules",
                {
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
        ),
        approval_protected_paths=list(
            cfg.get(
                "approval_protected_paths",
                [
                    "/opt/",
                    "/etc/",
                    "/boot/",
                    "/usr/",
                    "/bin/",
                    "/sbin/",
                ],
            )
        ),
        approval_high_risk_branches=list(
            cfg.get(
                "approval_high_risk_branches",
                [
                    "main",
                    "master",
                ],
            )
        ),
        approval_shell_safe_prefixes=list(
            cfg.get(
                "approval_shell_safe_prefixes",
                [
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
        ),
        approval_resource_keys=dict(
            cfg.get(
                "approval_resource_keys",
                {
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
        ),
        approval_dry_run_tools=list(
            cfg.get(
                "approval_dry_run_tools",
                [
                    "write_file",
                    "edit_file",
                    "delete_file",
                    "delete_directory",
                    "move_file",
                ],
            )
        ),
        sse_heartbeat_timeout=float(cfg.get("sse_heartbeat_timeout", 30.0)),
        sse_malformed_retry=int(cfg.get("sse_malformed_retry", 2)),
        sse_reconnect_max=int(cfg.get("sse_reconnect_max", 1)),
        llm_stream_retry_on_heartbeat_timeout=bool(
            cfg.get("llm_stream_retry_on_heartbeat_timeout", True)
        ),
        llm_stream_retry_on_malformed_chunk=bool(
            cfg.get("llm_stream_retry_on_malformed_chunk", False)
        ),
        tool_safety_tiers=dict(cfg.get("tool_safety_tiers", {})),
        allowed_root=cfg.get("allowed_root", ""),
        approval_github_allowed_repos=list(
            cfg.get("approval_github_allowed_repos", [])
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
    """Construct DbConfig from common.toml configuration via _get_cfg()."""
    cfg = _get_cfg()
    return DbConfig(
        rag_db_path=cfg.get("rag_db_path", ""),
        session_db_path=cfg.get("session_db_path", ""),
        sqlite_vec_so=cfg.get("sqlite_vec_so", ""),
        embed_url=cfg.get("embed_url", ""),
        sqlite_timeout=int(cfg.get("sqlite_timeout", 30)),
    )
