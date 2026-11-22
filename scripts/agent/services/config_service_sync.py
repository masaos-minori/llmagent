"""scripts/agent/services/config_service_sync.py — Service sync logic: propagates config changes to live service instances."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.context import AgentContext


@dataclass(frozen=True)
class SyncResult:
    """Result of ServiceSyncer.sync_all()."""

    applied: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


class ServiceSyncer:
    """Propagates config changes to live service instances.

    Accepts typed config objects (ctx.cfg.llm, ctx.cfg.tool)
    instead of _sync_services()'s current scalar-parameter signature.
    Preserves the exact ConfigReloadOutcome.applied entries.
    """

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    def sync_all(
        self,
        llm_cfg: Any,
        tool_cfg: Any,
    ) -> SyncResult:
        """Sync the two config sections to live services.

        Args:
            llm_cfg: LLM configuration object.
            tool_cfg: Tool configuration object.

        Returns:
            SyncResult with applied and skipped section names.
        """
        result = SyncResult()
        ctx = self._ctx

        if ctx.services_required.llm is not None:
            ctx.services_required.llm.apply_config(
                temperature=ctx.cfg.llm.llm_temperature,
                max_tokens=ctx.cfg.llm.llm_max_tokens,
                retry_base_delay=ctx.cfg.llm.llm_retry_base_delay,
                sse_heartbeat_timeout=ctx.cfg.llm.sse_heartbeat_timeout,
                sse_malformed_retry=ctx.cfg.llm.sse_malformed_retry,
                sse_reconnect_max=ctx.cfg.llm.sse_reconnect_max,
                stream_retry_on_heartbeat_timeout=ctx.cfg.llm.llm_stream_retry_on_heartbeat_timeout,
                stream_retry_on_malformed_chunk=ctx.cfg.llm.llm_stream_retry_on_malformed_chunk,
            )
            result.applied.append("llm")

        if ctx.services_required.hist_mgr is not None:
            ctx.services_required.hist_mgr.apply_config(
                char_limit=ctx.cfg.llm.context_char_limit,
                compress_turns=ctx.cfg.llm.context_compress_turns,
                token_limit=ctx.cfg.llm.context_token_limit,
                tokenize_url=ctx.cfg.llm.tokenize_url,
            )
            result.applied.append("hist_mgr")

        if ctx.services_required.runtime_tools is not None:
            # Agentcfg003 REQ-005/REQ-011: no tier_map is passed — the tier each
            # entry carries is the one its producer declared.
            ctx.services_required.runtime_tools.apply_policy(
                allowed_tools=ctx.cfg.tool.allowed_tools,
                tool_policy_mode=ctx.cfg.tool.tool_policy_mode,
                disabled_tools=ctx.cfg.tool.disabled_tools,
            )
            result.applied.append("runtime_tools")

        return result
