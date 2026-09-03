"""scripts/agent/services/config_reload.py

ConfigReloadService — applies reloaded configuration to live service instances.

Responsibilities:
  apply_config_dict()  — update ctx.cfg fields from raw dict and sync services
  _sync_services()     — propagate already-updated cfg to live service instances (private)

Both return ConfigReloadOutcome so callers can display what changed.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

from shared.mcp_config import McpServerConfig

from agent.config_dataclasses import AgentConfig
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.models import ConfigReloadRequest

if TYPE_CHECKING:
    from shared.runtime_tool import AgentSafetyTier
    from shared.runtime_tool_registry import RuntimeToolRegistry

    from agent.config_dataclasses import AgentConfig
    from agent.context import AgentContext
    from agent.history import HistoryManager
    from agent.llm_client import LLMClient

from agent.services.typed_validators import (
    _get_bool,
    _get_dict_nonempty,
    _get_float,
    _get_int,
    _get_list,
    _get_list_nonempty,
    _get_str,
    _get_str_nonempty,
)

# Magic string constants — replaces scattered literal field names
FIELD_HTTP_TIMEOUT = "http_timeout"
FIELD_CONTEXT_TOKEN_LIMIT = "context_token_limit"
FIELD_EMBED_URL = "embed_url"
FIELD_USE_SEMANTIC_CACHE = "use_semantic_cache"
FIELD_MAX_TOOL_TURNS = "max_tool_turns"
FIELD_TOOL_RESULT_MAX_LLM_CHARS = "tool_result_max_llm_chars"
FIELD_CONTEXT_CHAR_LIMIT = "context_char_limit"
FIELD_CONTEXT_COMPRESS_TURNS = "context_compress_turns"
FIELD_SERIAL_TOOL_CALLS = "serial_tool_calls"
FIELD_TOOL_DEFINITIONS_STRICT = "tool_definitions_strict"
FIELD_PLAN_BLOCKED_TOOLS = "plan_blocked_tools"
FIELD_LLML_TEMPERATURE = "llm_temperature"
FIELD_LLML_MAX_TOKENS = "llm_max_tokens"
FIELD_LLML_URL = "llm_url"
FIELD_WEB_SEARCH_URL = "web_search_url"
FIELD_LLML_MAX_RETRIES = "llm_max_retries"
FIELD_LLML_RETRY_BASE_DELAY = "llm_retry_base_delay"
FIELD_SSE_HEARTBEAT_TIMEOUT = "sse_heartbeat_timeout"
FIELD_SSE_MALFORMED_RETRY = "sse_malformed_retry"
FIELD_SSE_RECONNECT_MAX = "sse_reconnect_max"
FIELD_LLML_STREAM_RETRY_ON_HEARTBEAT_TIMEOUT = "llm_stream_retry_on_heartbeat_timeout"
FIELD_LLML_STREAM_RETRY_ON_MALFORMED_CHUNK = "llm_stream_retry_on_malformed_chunk"
FIELD_SYSTEM_PROMPT_TOOL = "system_prompt_tool"
FIELD_SYSTEM_PROMPTS = "system_prompts"
FIELD_TOOL_DEFINITIONS = "tool_definitions"
FIELD_SEMANTIC_CACHE_THRESHOLD = "semantic_cache_threshold"
FIELD_SEMANTIC_CACHE_MAX_SIZE = "semantic_cache_max_size"
FIELD_USE_REFINER = "use_refiner"
FIELD_REFINER_MAX_TOKENS = "refiner_max_tokens"
FIELD_REFINER_TIMEOUT = "refiner_timeout"
FIELD_REFINER_MAX_CHARS_PER_CHUNK = "refiner_max_chars_per_chunk"
FIELD_APPROVAL_RISK_RULES = "approval_risk_rules"
FIELD_APPROVAL_PROTECTED_PATHS = "approval_protected_paths"
FIELD_APPROVAL_HIGH_RISK_BRANCHES = "approval_high_risk_branches"
FIELD_APPROVAL_SHELL_SAFE_PREFIXES = "approval_shell_safe_prefixes"
FIELD_APPROVAL_RESOURCE_KEYS = "approval_resource_keys"
FIELD_APPROVAL_DRY_RUN_TOOLS = "approval_dry_run_tools"
FIELD_TOOL_SAFETY_TIERS = "tool_safety_tiers"
FIELD_ALLOWED_ROOT = "allowed_root"
FIELD_ALLOWED_TOOLS = "allowed_tools"
FIELD_APPROVAL_GITHUB_ALLOWED_REPOS = "approval_github_allowed_repos"
FIELD_GITOPS_PUSH_BLOCKED = "gitops_push_blocked"
FIELD_MEMORY_RETENTION_DAYS = "memory_retention_days"
FIELD_MEMORY_LOCAL_ONLY = "memory_local_only"
FIELD_SECURITY_PROFILE = "security_profile"
FIELD_SECURITY_LOCKDOWN_ENABLED = "security_lockdown_enabled"
FIELD_USE_MEMORY_LAYER = "use_memory_layer"
FIELD_ROUTING_DRIFT_STRICT = "routing_drift_strict"
FIELD_MEMORY_EMBED_ENABLED = "memory_embed_enabled"

_MCP_SERVER_FIELDS = (
    "transport",
    "url",
    "startup_mode",
    "call_timeout_sec",
    "startup_timeout_sec",
    "tool_names",
    "auth_token",
    "role",
    "cmd",
    "env",
)


def _diff_mcp_server_config(old: McpServerConfig, new: McpServerConfig) -> list[str]:
    """Return names of McpServerConfig fields that differ between old and new.

    Pure comparison — never mutates either argument. Field order follows
    _MCP_SERVER_FIELDS, so output is deterministic for a given pair of inputs.
    """
    return [
        field_name
        for field_name in _MCP_SERVER_FIELDS
        if getattr(old, field_name) != getattr(new, field_name)
    ]


@dataclass
class ConfigReloadOutcome:
    """Structured report of what changed after a /reload."""

    applied: list[str] = field(default_factory=list)
    needs_restart: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    """Fields intentionally ignored by /reload for reasons other than restart-

    required (e.g. unrecognized keys). MCP server definition changes are never
    reported here — see needs_restart instead."""
    source_files: list[str] = field(default_factory=list)
    startup_only: list[str] = field(default_factory=list)
    """Fields present in the reload payload and differing from the running
    value but requiring a restart to take effect. Distinct from `skipped`,
    which ignores fields for reasons unrelated to restart requirement, and
    `needs_restart`, which is reserved exclusively for MCP server definition
    changes."""
    always_live: list[str] = field(default_factory=list)
    """Fields that take effect independently of /reload — they are read from
    disk on every DiagnosticStore save()/fetch() call, so any change to them
    is immediately effective without a restart or special handling."""


class ConfigReloadService:
    """Propagate an updated config dict to live service instances.

    Called by _ConfigMixin._cmd_reload() after a fresh config is loaded.
    Updates ctx.cfg via typed validators, syncs services via their public APIs,
    and writes certain fields (e.g. system_prompt) directly to ctx.conv.
    """

    def __init__(self, ctx: AgentContext) -> None:
        """Initialize the config reload handler with the agent context for service updates."""
        self._ctx = ctx

    # ── Public entry point ────────────────────────────────────────────────────

    def apply_config(self, req: ConfigReloadRequest) -> ConfigReloadOutcome:
        """Convert a typed ConfigReloadRequest to a dict and delegate to apply_config_dict().

        Raises ConfigReloadValidationError on type-level field violations.
        """
        if req.masked_fields is not None and not isinstance(req.masked_fields, list):
            raise ConfigReloadValidationError(
                f"masked_fields must be a list, got {type(req.masked_fields).__name__}"
            )
        new_cfg = self._req_to_dict(req)
        return self.apply_config_dict(new_cfg)

    def apply_config_dict(self, new_cfg: dict[str, Any]) -> ConfigReloadOutcome:
        """Update ctx.cfg from new_cfg, sync live services, return a report.

        Replaces _apply_config_params() + all _apply_* helpers from _ConfigMixin.
        The command handler only calls this method and renders the result.
        """
        ctx = self._ctx
        self._collect_field_changes(new_cfg, {}, {}, {})
        self._apply_rag_tool_params(ctx, new_cfg)
        self._reload_approval_config(ctx, new_cfg)
        self._reload_tool_allowlist(ctx, new_cfg)
        self._reload_memory_runtime(ctx, new_cfg)
        self._reload_security_profile(ctx, new_cfg)
        if "masked_fields" in new_cfg:
            ctx.cfg.tool.masked_fields = list(new_cfg["masked_fields"])
        result = self._classify_mcp_server_changes(ctx, new_cfg)
        for item in result.needs_restart:
            if item.endswith(" (removed server)"):
                server_key = item.replace("mcp_servers/", "").removesuffix(
                    " (removed server)"
                )
                lifecycle = ctx.services_required.lifecycle
                if lifecycle is not None:
                    lifecycle.cleanup_server_resources(server_key)
        service_result = self._sync_services(
            new_cfg,
            ctx.services_required.llm,
            ctx.services_required.hist_mgr,
            ctx.services_required.runtime_tools,
        )
        result.applied.extend(service_result.applied)
        result.skipped.extend(service_result.skipped)
        result.startup_only = self._detect_startup_only(new_cfg)
        result.always_live = self._detect_diagnostics_live_fields(new_cfg)
        return result

    @staticmethod
    def _collect_field_changes(
        new_cfg: dict[str, Any],
        llm_changes: dict[str, Any],
        rag_changes: dict[str, Any],
        tool_changes: dict[str, Any],
    ) -> None:
        """Collect field values from new_cfg into change dicts for validation.

        Replaces _collect_request_values() and _apply_llm_prompt_params().
        Populates one unified set of change dicts.
        """
        # LLM fields
        if (v := _get_float(new_cfg, FIELD_HTTP_TIMEOUT)) is not None:
            llm_changes[FIELD_HTTP_TIMEOUT] = v
        if (v := _get_int(new_cfg, FIELD_CONTEXT_TOKEN_LIMIT)) is not None:
            llm_changes[FIELD_CONTEXT_TOKEN_LIMIT] = v
        if (temperature := _get_float(new_cfg, FIELD_LLML_TEMPERATURE)) is not None:
            llm_changes[FIELD_LLML_TEMPERATURE] = temperature
        if (max_tokens := _get_int(new_cfg, FIELD_LLML_MAX_TOKENS)) is not None:
            llm_changes[FIELD_LLML_MAX_TOKENS] = max_tokens
        if (llm_url := _get_str(new_cfg, FIELD_LLML_URL)) is not None:
            llm_changes[FIELD_LLML_URL] = llm_url
        if (max_retries := _get_int(new_cfg, FIELD_LLML_MAX_RETRIES)) is not None:
            llm_changes[FIELD_LLML_MAX_RETRIES] = max_retries
        if (base_delay := _get_float(new_cfg, FIELD_LLML_RETRY_BASE_DELAY)) is not None:
            llm_changes[FIELD_LLML_RETRY_BASE_DELAY] = base_delay

        # SSE fields
        if (vf := _get_float(new_cfg, FIELD_SSE_HEARTBEAT_TIMEOUT)) is not None:
            llm_changes[FIELD_SSE_HEARTBEAT_TIMEOUT] = vf
        if (vi := _get_int(new_cfg, FIELD_SSE_MALFORMED_RETRY)) is not None:
            llm_changes[FIELD_SSE_MALFORMED_RETRY] = vi
        if (vi := _get_int(new_cfg, FIELD_SSE_RECONNECT_MAX)) is not None:
            llm_changes[FIELD_SSE_RECONNECT_MAX] = vi
        if (
            vb := _get_bool(new_cfg, FIELD_LLML_STREAM_RETRY_ON_HEARTBEAT_TIMEOUT)
        ) is not None:
            llm_changes[FIELD_LLML_STREAM_RETRY_ON_HEARTBEAT_TIMEOUT] = vb
        if (
            vb := _get_bool(new_cfg, FIELD_LLML_STREAM_RETRY_ON_MALFORMED_CHUNK)
        ) is not None:
            llm_changes[FIELD_LLML_STREAM_RETRY_ON_MALFORMED_CHUNK] = vb

        # RAG fields
        if (embed_url := _get_str(new_cfg, FIELD_EMBED_URL)) is not None:
            rag_changes[FIELD_EMBED_URL] = embed_url
        if (vb := _get_bool(new_cfg, FIELD_USE_SEMANTIC_CACHE)) is not None:
            rag_changes[FIELD_USE_SEMANTIC_CACHE] = vb
        if (web_search_url := _get_str(new_cfg, FIELD_WEB_SEARCH_URL)) is not None:
            rag_changes[FIELD_WEB_SEARCH_URL] = web_search_url
        if (vf := _get_float(new_cfg, FIELD_SEMANTIC_CACHE_THRESHOLD)) is not None:
            rag_changes[FIELD_SEMANTIC_CACHE_THRESHOLD] = vf
        if (vi := _get_int(new_cfg, FIELD_SEMANTIC_CACHE_MAX_SIZE)) is not None:
            rag_changes[FIELD_SEMANTIC_CACHE_MAX_SIZE] = vi
        if (vb := _get_bool(new_cfg, FIELD_USE_REFINER)) is not None:
            rag_changes[FIELD_USE_REFINER] = vb
        if (v := _get_int(new_cfg, FIELD_REFINER_MAX_TOKENS)) is not None:
            rag_changes[FIELD_REFINER_MAX_TOKENS] = v
        if (v := _get_float(new_cfg, FIELD_REFINER_TIMEOUT)) is not None:
            rag_changes[FIELD_REFINER_TIMEOUT] = v
        if (v := _get_int(new_cfg, FIELD_REFINER_MAX_CHARS_PER_CHUNK)) is not None:
            rag_changes[FIELD_REFINER_MAX_CHARS_PER_CHUNK] = v

        # Tool fields
        if (v := _get_int(new_cfg, FIELD_MAX_TOOL_TURNS)) is not None:
            tool_changes[FIELD_MAX_TOOL_TURNS] = v
        if (
            tool_result_max_chars := _get_int(new_cfg, FIELD_TOOL_RESULT_MAX_LLM_CHARS)
        ) is not None:
            tool_changes[FIELD_TOOL_RESULT_MAX_LLM_CHARS] = tool_result_max_chars
        if (lst := _get_list_nonempty(new_cfg, FIELD_TOOL_DEFINITIONS)) is not None:
            tool_changes[FIELD_TOOL_DEFINITIONS] = list(lst)
        if (
            prompt_tool := _get_str_nonempty(new_cfg, FIELD_SYSTEM_PROMPT_TOOL)
        ) is not None:
            tool_changes[FIELD_SYSTEM_PROMPT_TOOL] = prompt_tool
        if (
            sys_prompts := _get_dict_nonempty(new_cfg, FIELD_SYSTEM_PROMPTS)
        ) is not None:
            tool_changes[FIELD_SYSTEM_PROMPTS] = dict(sys_prompts)
        if (vb := _get_bool(new_cfg, FIELD_SERIAL_TOOL_CALLS)) is not None:
            tool_changes[FIELD_SERIAL_TOOL_CALLS] = vb
        if (vb := _get_bool(new_cfg, FIELD_TOOL_DEFINITIONS_STRICT)) is not None:
            tool_changes[FIELD_TOOL_DEFINITIONS_STRICT] = vb
        if (lst := _get_list(new_cfg, FIELD_PLAN_BLOCKED_TOOLS)) is not None:
            tool_changes[FIELD_PLAN_BLOCKED_TOOLS] = list(lst)

    @staticmethod
    def _req_to_dict(req: ConfigReloadRequest) -> dict[str, Any]:
        """Convert ConfigReloadRequest to the raw dict format expected by _apply_* helpers."""
        d: dict[str, Any] = {}
        if req.mcp_servers is not None:
            d["mcp_servers"] = req.mcp_servers
        if req.approval is not None:
            d["approval"] = req.approval
        if req.llm is not None:
            d.update(req.llm)
        if req.masked_fields is not None:
            d["masked_fields"] = req.masked_fields
        if req.rag_tool is not None:
            d.update(req.rag_tool)
        if req.sse is not None:
            d.update(req.sse)
        return d

    # ── Service sync ──────────────────────────────────────────────────────────

    def _sync_services(
        self,
        new_cfg: dict[str, Any],
        llm_service: LLMClient | None,
        hist_mgr_service: HistoryManager | None,
        runtime_tools_service: RuntimeToolRegistry | None,
    ) -> ConfigReloadOutcome:
        """Apply new_cfg values to running service instances; return a report."""
        result = ConfigReloadOutcome()
        ctx = self._ctx

        if llm_service is not None:
            llm_service.apply_config(
                temperature=ctx.cfg.llm.llm_temperature,
                max_tokens=ctx.cfg.llm.llm_max_tokens,
                max_retries=ctx.cfg.llm.llm_max_retries,
                retry_base_delay=ctx.cfg.llm.llm_retry_base_delay,
                sse_heartbeat_timeout=ctx.cfg.llm.sse_heartbeat_timeout,
                sse_malformed_retry=ctx.cfg.llm.sse_malformed_retry,
                sse_reconnect_max=ctx.cfg.llm.sse_reconnect_max,
                stream_retry_on_heartbeat_timeout=ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout,
                stream_retry_on_malformed_chunk=ctx.cfg.llm.llm_stream_retry_on_malformed_chunk,
            )
            result.applied.append("llm")

        if hist_mgr_service is not None:
            hist_mgr_service.apply_config(
                char_limit=ctx.cfg.llm.context_char_limit,
                compress_turns=ctx.cfg.llm.context_compress_turns,
                token_limit=ctx.cfg.llm.context_token_limit,
                tokenize_url=ctx.cfg.llm.tokenize_url,
            )
            result.applied.append("hist_mgr")

        if runtime_tools_service is not None:
            runtime_tools_service.apply_policy(
                tier_map=cast(
                    Mapping[str, "AgentSafetyTier"], ctx.cfg.approval.tool_safety_tiers
                ),
                allowed_tools=ctx.cfg.tool.allowed_tools,
            )
            result.applied.append("runtime_tools")

        # system_prompt update: write to the canonical field; Orchestrator syncs history[0].
        if FIELD_SYSTEM_PROMPT_TOOL in new_cfg:
            ctx.conv.system_prompt_content = new_cfg[FIELD_SYSTEM_PROMPT_TOOL]

        return result

    # ── cfg-field update helpers (moved from _ConfigMixin) ────────────────────

    def _apply_rag_tool_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> ConfigReloadOutcome:
        """Apply LLM/RAG/Tool settings with validation re-execution."""
        result = ConfigReloadOutcome()
        cfg = ctx.cfg

        llm_changes: dict[str, Any] = {}
        rag_changes: dict[str, Any] = {}
        tool_changes: dict[str, Any] = {}

        self._apply_llm_context_params(cfg, new_cfg, llm_changes)
        self._apply_tool_params(cfg, new_cfg, tool_changes)
        self._apply_rag_params(cfg, new_cfg, rag_changes)
        self._apply_llm_retry_params(cfg, new_cfg, llm_changes)
        self._apply_llm_prompt_params(
            ctx, new_cfg, llm_changes, rag_changes, tool_changes
        )
        self._apply_sse_reload_params(ctx, new_cfg, llm_changes)

        if llm_changes:
            try:
                new_llm = dataclasses.replace(cfg.llm, **llm_changes)
            except ValueError as e:
                raise ConfigReloadValidationError(str(e)) from e
            # Re-validate after replacement
            from agent.services.config_validators import (
                validate_llm_context_char_limit,
                validate_llm_max_retries,
                validate_llm_max_tokens,
                validate_llm_retry_base_delay,
                validate_llm_sse_heartbeat_timeout,
                validate_llm_sse_malformed_retry,
                validate_llm_sse_reconnect_max,
                validate_llm_temperature,
            )

            validate_llm_temperature(new_llm)
            validate_llm_max_tokens(new_llm)
            validate_llm_context_char_limit(new_llm)
            validate_llm_max_retries(new_llm)
            validate_llm_retry_base_delay(new_llm)
            validate_llm_sse_heartbeat_timeout(new_llm)
            validate_llm_sse_malformed_retry(new_llm)
            validate_llm_sse_reconnect_max(new_llm)
            cfg.llm = new_llm

        if rag_changes:
            # Remove undeclared fields that cannot go through dataclasses.replace()
            rag_changes = {
                k: v for k, v in rag_changes.items() if k != "web_search_url"
            }
            if rag_changes:
                try:
                    new_rag = dataclasses.replace(cfg.rag, **rag_changes)
                except ValueError as e:
                    raise ConfigReloadValidationError(str(e)) from e
                from agent.services.config_validators import (
                    validate_rag_refiner_max_chars_per_chunk,
                    validate_rag_refiner_max_tokens,
                    validate_rag_refiner_timeout,
                )

                validate_rag_refiner_max_tokens(new_rag)
                validate_rag_refiner_timeout(new_rag)
                validate_rag_refiner_max_chars_per_chunk(new_rag)
                cfg.rag = new_rag

        if tool_changes:
            try:
                new_tool = dataclasses.replace(cfg.tool, **tool_changes)
            except ValueError as e:
                raise ConfigReloadValidationError(str(e)) from e
            from agent.services.config_validators import (
                validate_progress_stagnation_window,
                validate_tool_cycle_detect_window,
                validate_tool_dedup_max_repeats,
                validate_tool_error_max_consecutive,
                validate_tool_error_retry_max,
            )

            validate_tool_dedup_max_repeats(new_tool)
            validate_tool_cycle_detect_window(new_tool)
            validate_tool_error_max_consecutive(new_tool)
            validate_tool_error_retry_max(new_tool)
            validate_progress_stagnation_window(new_tool)
            cfg.tool = new_tool

        return result

    def _apply_llm_context_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect LLM context window setting changes."""
        if (v := _get_int(new_cfg, "context_char_limit")) is not None:
            changes["context_char_limit"] = v
        if (v := _get_int(new_cfg, "context_compress_turns")) is not None:
            changes["context_compress_turns"] = v

    def _apply_tool_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect tool execution setting changes."""
        if (vb := _get_bool(new_cfg, "serial_tool_calls")) is not None:
            changes["serial_tool_calls"] = vb
        if (vb := _get_bool(new_cfg, "tool_definitions_strict")) is not None:
            changes["tool_definitions_strict"] = vb
        if (lst := _get_list(new_cfg, "plan_blocked_tools")) is not None:
            changes["plan_blocked_tools"] = list(lst)

    def _apply_rag_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect RAG setting changes."""
        if (vb := _get_bool(new_cfg, "use_semantic_cache")) is not None:
            changes["use_semantic_cache"] = vb
        if (v := _get_float(new_cfg, "semantic_cache_threshold")) is not None:
            changes["semantic_cache_threshold"] = v
        if (v := _get_int(new_cfg, "semantic_cache_max_size")) is not None:
            changes["semantic_cache_max_size"] = v
        if (vb := _get_bool(new_cfg, "use_refiner")) is not None:
            changes["use_refiner"] = vb
        if (v := _get_int(new_cfg, "refiner_max_tokens")) is not None:
            changes["refiner_max_tokens"] = v
        if (v := _get_float(new_cfg, "refiner_timeout")) is not None:
            changes["refiner_timeout"] = v
        if (v := _get_int(new_cfg, "refiner_max_chars_per_chunk")) is not None:
            changes["refiner_max_chars_per_chunk"] = v

    def _apply_llm_retry_params(
        self, cfg: AgentConfig, new_cfg: dict[str, Any], changes: dict[str, Any]
    ) -> None:
        """Collect LLM retry setting changes."""
        if (max_retries := _get_int(new_cfg, "llm_max_retries")) is not None:
            changes["llm_max_retries"] = max_retries
        if (base_delay := _get_float(new_cfg, "llm_retry_base_delay")) is not None:
            changes["llm_retry_base_delay"] = base_delay

    def _classify_mcp_server_changes(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> ConfigReloadOutcome:
        """Classify MCP server definition changes as restart-required, field by field.

        MCP server definitions are restart-time snapshots: ToolExecutor and
        HttpTransport are built from them at startup, so mutating
        `ctx.cfg.mcp.mcp_servers` here would desync already-running instances
        from the reported config. This method only compares; it never writes.
        """
        from agent.config_builders import (
            _build_mcp_servers,  # lazy: avoids circular import at module level
        )

        result = ConfigReloadOutcome()
        new_mcp = _build_mcp_servers(new_cfg)
        old_mcp = ctx.cfg.mcp.mcp_servers
        for key, new_srv in new_mcp.items():
            old_srv = old_mcp.get(key)
            if old_srv is None:
                result.needs_restart.append(f"mcp_servers/{key} (new server)")
                continue
            for field_name in _diff_mcp_server_config(old_srv, new_srv):
                result.needs_restart.append(f"mcp_servers/{key}.{field_name}")
        for key in old_mcp:
            if key not in new_mcp:
                result.needs_restart.append(f"mcp_servers/{key} (removed server)")
        return result

    def _apply_llm_prompt_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
        llm_changes: dict[str, Any],
        rag_changes: dict[str, Any],
        tool_changes: dict[str, Any],
    ) -> None:
        """Collect hot-reloadable URL, HTTP, LLM generation, tool definition, and prompt settings."""
        if (temperature := _get_float(new_cfg, "llm_temperature")) is not None:
            llm_changes["llm_temperature"] = temperature
        if (max_tokens := _get_int(new_cfg, "llm_max_tokens")) is not None:
            llm_changes["llm_max_tokens"] = max_tokens
        if (llm_url := _get_str(new_cfg, "llm_url")) is not None:
            llm_changes["llm_url"] = llm_url
        if (web_search_url := _get_str(new_cfg, "web_search_url")) is not None:
            rag_changes["web_search_url"] = web_search_url
        if (embed_url := _get_str(new_cfg, "embed_url")) is not None:
            rag_changes["embed_url"] = embed_url
        if (http_timeout := _get_float(new_cfg, "http_timeout")) is not None:
            llm_changes["http_timeout"] = http_timeout
        if (max_tool_turns := _get_int(new_cfg, "max_tool_turns")) is not None:
            tool_changes["max_tool_turns"] = max_tool_turns
        if (
            tool_result_max_chars := _get_int(new_cfg, "tool_result_max_llm_chars")
        ) is not None:
            tool_changes["tool_result_max_llm_chars"] = tool_result_max_chars
        if (lst := _get_list_nonempty(new_cfg, "tool_definitions")) is not None:
            tool_changes["tool_definitions"] = list(lst)
        if (
            prompt_tool := _get_str_nonempty(new_cfg, "system_prompt_tool")
        ) is not None:
            tool_changes["system_prompt_tool"] = prompt_tool
        if (sys_prompts := _get_dict_nonempty(new_cfg, "system_prompts")) is not None:
            tool_changes["system_prompts"] = dict(sys_prompts)

    def _apply_sse_reload_params(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
        changes: dict[str, Any],
    ) -> None:
        """Collect SSE stream resilience settings."""
        if (vf := _get_float(new_cfg, "sse_heartbeat_timeout")) is not None:
            changes["sse_heartbeat_timeout"] = vf
        if (vi := _get_int(new_cfg, "sse_malformed_retry")) is not None:
            changes["sse_malformed_retry"] = vi
        if (vi := _get_int(new_cfg, "sse_reconnect_max")) is not None:
            changes["sse_reconnect_max"] = vi
        if (
            vb := _get_bool(new_cfg, "llm_stream_retry_on_heartbeat_timeout")
        ) is not None:
            changes["llm_stream_retry_on_heartbeat_timeout"] = vb
        if (
            vb := _get_bool(new_cfg, "llm_stream_retry_on_malformed_chunk")
        ) is not None:
            changes["llm_stream_retry_on_malformed_chunk"] = vb

    def _reload_section(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
        section_path: str,
        field_mappings: list[tuple[str, str]],
    ) -> None:
        """Apply a batch of field updates to a config section.

        Args:
            ctx: AgentContext for accessing cfg
            new_cfg: New configuration dict
            section_path: Dot-separated path to the target section (e.g., "approval")
            field_mappings: List of (new_cfg_key, target_field) tuples where
                target_field is the attribute name within the section
        """
        parts = section_path.split(".")
        obj = ctx.cfg
        for part in parts:
            obj = getattr(obj, part)
        for new_key, target_field in field_mappings:
            if new_key not in new_cfg:
                continue
            value = new_cfg[new_key]
            if isinstance(value, dict):
                setattr(obj, target_field, dict(value))
            elif isinstance(value, list):
                setattr(obj, target_field, list(value))
            else:
                setattr(obj, target_field, value)

    def _reload_approval_config(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Update ApprovalConfig fields in ctx.cfg when present in new_cfg."""
        field_mappings = [
            (FIELD_APPROVAL_RISK_RULES, "approval_risk_rules"),
            (FIELD_APPROVAL_PROTECTED_PATHS, "approval_protected_paths"),
            (FIELD_APPROVAL_HIGH_RISK_BRANCHES, "approval_high_risk_branches"),
            (FIELD_APPROVAL_SHELL_SAFE_PREFIXES, "approval_shell_safe_prefixes"),
            (FIELD_APPROVAL_RESOURCE_KEYS, "approval_resource_keys"),
            (FIELD_APPROVAL_DRY_RUN_TOOLS, "approval_dry_run_tools"),
            (FIELD_TOOL_SAFETY_TIERS, "tool_safety_tiers"),
            (FIELD_ALLOWED_ROOT, "allowed_root"),
            (FIELD_APPROVAL_GITHUB_ALLOWED_REPOS, "approval_github_allowed_repos"),
            (FIELD_GITOPS_PUSH_BLOCKED, "gitops_push_blocked"),
        ]
        self._reload_section(ctx, new_cfg, "approval", field_mappings)

    def _reload_tool_allowlist(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload allowed_tools from new_cfg if present."""
        self._reload_section(
            ctx, new_cfg, "tool", [(FIELD_ALLOWED_TOOLS, "allowed_tools")]
        )

    def _reload_memory_runtime(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload memory runtime fields from new_cfg if present."""
        field_mappings = [
            (FIELD_MEMORY_RETENTION_DAYS, "memory_retention_days"),
            (FIELD_MEMORY_LOCAL_ONLY, "memory_local_only"),
        ]
        self._reload_section(ctx, new_cfg, "memory", field_mappings)

    def _reload_security_profile(
        self,
        ctx: AgentContext,
        new_cfg: dict[str, Any],
    ) -> None:
        """Reload security profile fields from new_cfg if present."""
        if (vs := _get_str(new_cfg, FIELD_SECURITY_PROFILE)) is not None:
            try:
                from shared.mcp_config import SecurityProfile

                ctx.cfg.mcp.security_profile = SecurityProfile(vs)
            except ValueError:
                pass  # invalid enum value — leave current
        if (vb := _get_bool(new_cfg, FIELD_SECURITY_LOCKDOWN_ENABLED)) is not None:
            ctx.cfg.mcp.security_lockdown_enabled = vb

    def _detect_startup_only(
        self,
        new_cfg: dict[str, Any],
    ) -> list[str]:
        """Return names of startup-only fields that differ between new_cfg and running cfg."""
        changed: list[str] = []
        ctx = self._ctx
        v = _get_bool(new_cfg, "use_memory_layer")
        if v is not None and v != ctx.cfg.memory.use_memory_layer:
            changed.append("use_memory_layer")

        v = _get_bool(new_cfg, "routing_drift_strict")
        if v is not None and v != ctx.cfg.tool.routing_drift_strict:
            changed.append("routing_drift_strict")

        v = _get_bool(new_cfg, "memory_embed_enabled")
        if v is not None and v != ctx.cfg.memory.memory_embed_enabled:
            changed.append("memory_embed_enabled")
        return changed

    def _detect_diagnostics_live_fields(
        self,
        new_cfg: dict[str, Any],
    ) -> list[str]:
        """Return names of diagnostics.* fields that differ between new_cfg and running cfg.

        These fields take effect immediately on every DiagnosticStore save()/fetch()
        call, independent of /reload — they are config-file-driven, not startup-only.
        """
        changed: list[str] = []
        ctx = self._ctx
        diag_new = new_cfg.get("diagnostics")
        if diag_new is None:
            return changed
        diag_running = getattr(ctx.cfg, "diagnostics", None)
        if diag_running is None:
            return changed
        for key in ("encryption_key", "retention_days", "sensitive_fields"):
            v = diag_new.get(key)
            if v is None:
                continue
            current = getattr(diag_running, key, None)
            if v != current:
                changed.append(f"diagnostics.{key}")
        return changed
