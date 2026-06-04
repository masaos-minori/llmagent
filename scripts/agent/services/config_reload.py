"""agent/services/config_reload.py
ConfigReloadService — applies reloaded configuration to live service instances.

Extracts the service-synchronization responsibility from cmd_config._ConfigMixin
so command handlers never write to private service attributes directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.context import AgentContext


@dataclass
class ConfigReloadResult:
    """Structured report of what changed after a /reload."""

    applied: list[str] = field(default_factory=list)
    needs_restart: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class ConfigReloadService:
    """Propagate an updated config dict to live service instances.

    Called by _ConfigMixin._cmd_reload() after a fresh config is loaded.
    Uses public apply_config() APIs on each service — never writes private attrs.
    """

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    def sync_services(self, new_cfg: dict[str, Any]) -> ConfigReloadResult:
        """Apply new_cfg values to running service instances; return a report."""
        result = ConfigReloadResult()
        ctx = self._ctx

        if ctx.services.llm is not None:
            ctx.services.llm.apply_config(
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

        if ctx.services.hist_mgr is not None:
            ctx.services.hist_mgr.apply_config(
                char_limit=ctx.cfg.llm.context_char_limit,
                compress_turns=ctx.cfg.llm.context_compress_turns,
                token_limit=ctx.cfg.llm.context_token_limit,
                tokenize_url=ctx.cfg.llm.tokenize_url,
            )
            result.applied.append("hist_mgr")

        if ctx.services.tools is not None:
            ctx.services.tools.apply_config(cache_ttl=ctx.cfg.tool.tool_cache_ttl)
            result.applied.append("tools")

        # system_prompt update: write to the canonical field; Orchestrator syncs history[0].
        if "system_prompt_tool" in new_cfg:
            ctx.system_prompt_content = new_cfg["system_prompt_tool"]

        return result
