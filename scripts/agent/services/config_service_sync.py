"""scripts/agent/services/config_service_sync.py — Service sync logic: propagates config changes to live service instances.

`prepare_llm` and `prepare_runtime_tools` capture the live service state and return
the transaction step that applies the change, so the reload transaction can commit
it and undo it (REQ-006).  They are the only service-apply path: the reload commits
through the transaction, which drives these steps (REQ-013).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shared.config_undo import UndoToken
from shared.llm_hot_config import LlmHotConfigHandler

from agent.services.config_reload_transaction import PreparedStep

if TYPE_CHECKING:
    from agent.context import AgentContext

# Config keys each service step writes. The rollback report names these, never the
# values they carry (REQ-011).
_LLM_SYNC_FIELDS: tuple[str, ...] = (
    "llm_temperature",
    "llm_max_tokens",
    "llm_retry_base_delay",
    "sse_heartbeat_timeout",
    "sse_malformed_retry",
    "sse_reconnect_max",
    "llm_stream_retry_on_heartbeat_timeout",
    "llm_stream_retry_on_malformed_chunk",
)
_TOOL_POLICY_FIELDS: tuple[str, ...] = (
    "allowed_tools",
    "tool_policy_mode",
    "disabled_tools",
)


class ServiceSyncer:
    """Propagates config changes to live service instances.

    Accepts typed config objects (ctx.cfg.llm, ctx.cfg.tool) and returns one
    reversible step per service, so the transaction keeps the exact
    ConfigReloadOutcome.applied entries.
    """

    def __init__(self, ctx: AgentContext) -> None:
        self._ctx = ctx

    def prepare_llm(self) -> PreparedStep | None:
        """Capture the live LLM state and return the step that applies the hot-config values.

        The snapshot is taken here, before any mutation, so the step's undo token
        restores the values this reload replaced (REQ-006).  Returns None when no
        LLM client is wired.
        """
        llm = self._ctx.services_required.llm
        if llm is None:
            return None
        snapshot = LlmHotConfigHandler.snapshot(llm)

        def apply() -> UndoToken:
            # Read the section at commit time: the section steps run first, so the
            # values this step writes are the candidate values the section commit wrote.
            cfg = self._ctx.cfg.llm
            llm.apply_config(
                temperature=cfg.llm_temperature,
                max_tokens=cfg.llm_max_tokens,
                retry_base_delay=cfg.llm_retry_base_delay,
                sse_heartbeat_timeout=cfg.sse_heartbeat_timeout,
                sse_malformed_retry=cfg.sse_malformed_retry,
                sse_reconnect_max=cfg.sse_reconnect_max,
                stream_retry_on_heartbeat_timeout=cfg.llm_stream_retry_on_heartbeat_timeout,
                stream_retry_on_malformed_chunk=cfg.llm_stream_retry_on_malformed_chunk,
            )
            return UndoToken(
                service="llm",
                field_paths=_LLM_SYNC_FIELDS,
                restore=lambda: LlmHotConfigHandler.restore(llm, snapshot),
            )

        return PreparedStep(
            service="llm",
            field_paths=_LLM_SYNC_FIELDS,
            apply=apply,
        )

    def prepare_runtime_tools(self) -> PreparedStep | None:
        """Capture the registry tool mapping and return the step that reapplies the tool policy.

        Agentcfg003 REQ-005/REQ-011: no tier_map is passed — the tier each entry
        carries is the one its producer declared.  Returns None when no registry is
        wired.
        """
        registry = self._ctx.services_required.runtime_tools
        if registry is None:
            return None
        snapshot = registry.snapshot_policy()

        def apply() -> UndoToken:
            # Read the section at commit time: the tool section step runs first, so
            # the policy this step applies is the candidate policy the section wrote.
            tool = self._ctx.cfg.tool
            registry.apply_policy(
                allowed_tools=tool.allowed_tools,
                tool_policy_mode=tool.tool_policy_mode,
                disabled_tools=tool.disabled_tools,
            )
            return UndoToken(
                service="runtime_tools",
                field_paths=_TOOL_POLICY_FIELDS,
                restore=lambda: registry.restore_policy(snapshot),
            )

        return PreparedStep(
            service="runtime_tools",
            field_paths=_TOOL_POLICY_FIELDS,
            apply=apply,
        )
