"""scripts/agent/services/config_reload.py

ConfigReloadService — thin orchestrator over extracted sub-modules.

Responsibilities:
  apply_config_dict()  — build the reload candidate, prepare every change, and drive
                         the ReloadTransaction that commits or rolls them back
  _pending_state()     — read the container's PendingConfigState (private)

Every path returns ConfigReloadOutcome so callers can display what changed and which
stage the reload ended in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from shared.config_undo import UndoToken

from agent.config_builders import agent_config_payload, build_agent_config
from agent.prompt_source import load_prompt_source
from agent.services.config_outcome_classification import (
    PendingChange,
    classify_startup_only_fields,
    detect_diagnostics_live_fields,
    diff_mcp_definitions,
)
from agent.services.config_pending_state import (
    PendingConfigState,
    PendingMcpRecord,
    pending_state_for,
)
from agent.services.config_reload_transaction import (
    CommitPhase,
    PreparedStep,
    ReloadStage,
    ReloadTransaction,
)
from agent.services.config_section_reload import (
    apply_validated_section,
    prepare_validated_section,
)
from agent.services.config_service_sync import ServiceSyncer
from agent.services.exceptions import (
    ConfigReloadRollbackError,
    ConfigReloadValidationError,
)
from agent.services.models import ConfigReloadRequest

if TYPE_CHECKING:
    from agent.config_dataclasses import AgentConfig
    from agent.context import AgentContext
    from agent.services.config_section_reload import SectionCandidate

# Suffix the CLI prints for an MCP definition record that names a whole server.
_MCP_RECORD_SUFFIXES: dict[str, str] = {
    "added": " (new server)",
    "removed": " (removed server)",
}

# The conversation prompt is applied by a commit step but is not a configuration
# section, so it stays out of the outcome's applied list (unchanged CLI contract).
_CONVERSATION_SERVICE = "conversation"


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
    stage: ReloadStage = ReloadStage.PREPARED
    """Stage the reload ended in.  `prepared` covers the no-change and
    pending-only cases; `committed` means every applied step is live.  A commit
    or rollback failure raises instead of returning, so `rolled_back` and
    `degraded` appear on the raised error path (REQ-005)."""


def _prepare_section_candidates(
    ctx: AgentContext, candidate: AgentConfig
) -> list[SectionCandidate]:
    """Prepare one candidate per section the candidate changes, without mutating ctx.

    `masked_fields` is not a registry field, so it stays on the `extra_changed_fields`
    path rather than going through the field registry.
    """
    prepared: list[SectionCandidate] = []
    for section_path in ("llm", "tool", "approval", "memory"):
        extra: dict[str, Any] | None = None
        if (
            section_path == "tool"
            and candidate.tool.masked_fields != ctx.cfg.tool.masked_fields
        ):
            extra = {"masked_fields": list(candidate.tool.masked_fields)}
        section_candidate = prepare_validated_section(
            ctx,
            section_path,
            getattr(candidate, section_path),
            extra_changed_fields=extra,
        )
        if section_candidate is not None:
            prepared.append(section_candidate)
    return prepared


def _section_step(ctx: AgentContext, candidate: SectionCandidate) -> PreparedStep:
    """Return the commit step that writes one prepared section candidate onto ctx.cfg.

    The closure binds the candidate explicitly instead of capturing the loop
    variable through a default argument, so each step keeps its own candidate and
    the apply signature stays typed.
    """

    def apply() -> UndoToken:
        return apply_validated_section(ctx, candidate)

    return PreparedStep(
        service=candidate.section_path,
        field_paths=candidate.field_paths,
        apply=apply,
    )


class ConfigReloadService:
    """Propagate an updated config dict to live service instances.

    Called by _ConfigMixin._cmd_reload() after a fresh config is loaded.
    Builds a typed candidate through the startup parser, applies it to ctx.cfg,
    syncs services via their public APIs, and writes certain fields (e.g.
    system_prompt) directly to ctx.conv.
    """

    def __init__(self, ctx: AgentContext) -> None:
        """Initialize the config reload handler with the agent context for service updates."""
        self._ctx = ctx
        self._degraded_services: tuple[str, ...] = ()

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
        """Update ctx.cfg from new_cfg, commit through the transaction, return a report.

        Three phases, in this order:
          Candidate phase — build one typed ``AgentConfig`` through
          ``build_agent_config(cfg_override=...)``, the same production
          validation and section assembly startup runs, then prepare every
          section, the startup-only classification, the MCP classification, and
          the prompt source from it, without mutating live state. A
          ``ConfigReloadValidationError`` from any of them aborts here, leaving
          ctx.cfg and ctx.conv untouched.
          Prepare phase — register one reversible step per change, each carrying
          the snapshot its service captured before any mutation.  Still no live
          mutation.
          Commit phase — ``ReloadTransaction.commit()`` applies the steps in the
          fixed order (section values, conversation prompt content, runtime tool
          policy, history limits, llm hot-config) and records one undo token per
          applied step.  A step that raises is followed by a reverse-order
          rollback (REQ-005, REQ-006).

        The payload is applied on top of the live configuration: the live config
        is rendered back into the payload shape and ``new_cfg`` overrides it, so
        the candidate is always a complete configuration and a payload that names
        one field changes only that field (REQ-002).

        The outcome report shape (applied, needs_restart, skipped,
        startup_only, always_live) is unchanged; ``stage`` is new.

        Raises:
            ConfigReloadValidationError: A candidate-phase rule failed; nothing
                was mutated.
            ConfigReloadCommitError: A commit step failed and every applied step
                was undone.
            ConfigReloadRollbackError: A rollback step failed, leaving live state
                inconsistent, or a previous reload on this service already left
                it inconsistent (REQ-012).
        """
        ctx = self._ctx
        outcome = ConfigReloadOutcome()

        # A reload that ended `degraded` left a live service inconsistent: a later
        # reload would commit on top of that state (REQ-012).  The pending state
        # carries the record across commands; `self._degraded_services` carries it
        # within this service instance.
        pending = self._pending_state()
        self._refuse_if_degraded(pending)

        # ── Candidate phase: build + validate everything; no live mutation ──
        candidate = build_agent_config(
            cfg_override={**agent_config_payload(ctx.cfg), **new_cfg}
        )

        prepared = _prepare_section_candidates(ctx, candidate)

        # Classified before any mutation, so the comparison sees the running
        # values rather than values this reload already wrote (REQ-003).
        startup_only_records = classify_startup_only_fields(ctx, candidate)
        mcp_records = diff_mcp_definitions(ctx.cfg.mcp, candidate.mcp)
        self._record_pending_candidate(pending, startup_only_records, mcp_records)

        # ── Prepare phase: register reversible steps; still no live mutation ──
        txn = ReloadTransaction()
        for section_candidate in prepared:
            txn.add_step(CommitPhase.SECTIONS, _section_step(ctx, section_candidate))

        # Read boundary of the single source (agent.prompt_source): the read and
        # the comparison happen here, before any mutation, so a missing or
        # invalid source raises in the candidate phase and mutates nothing.
        resolved_prompt = load_prompt_source().content(ctx.conv.system_prompt_name)
        if resolved_prompt != ctx.conv.system_prompt_content:
            txn.add_step(CommitPhase.CONVERSATION, self._prompt_step(resolved_prompt))

        syncer = ServiceSyncer(ctx)
        runtime_tools_step = syncer.prepare_runtime_tools()
        if runtime_tools_step is not None:
            txn.add_step(CommitPhase.RUNTIME_TOOLS, runtime_tools_step)

        # No HistoryManager step: every value the manager reads from a reload
        # (context_char_limit, context_compress_turns, context_token_limit,
        # tokenize_url) is startup-only, so a reload can never change them and a
        # step would only claim an apply that did not happen (REQ-003, AC-2).

        llm_step = syncer.prepare_llm()
        if llm_step is not None:
            txn.add_step(CommitPhase.LLM_CONFIG, llm_step)

        # ── Commit phase: the transaction owns the order and the rollback ──
        try:
            txn.commit()
        except ConfigReloadRollbackError:
            self._degraded_services = txn.degraded_services
            if pending is not None:
                pending.record_degraded(txn.degraded_services)
            raise

        outcome.applied.extend(
            service for service in txn.applied if service != _CONVERSATION_SERVICE
        )
        outcome.stage = txn.stage
        for record in mcp_records:
            outcome.needs_restart.extend(_mcp_record_display(record))
        outcome.startup_only = [record.field_path for record in startup_only_records]
        outcome.always_live = self._detect_diagnostics_live_fields(new_cfg)
        return outcome

    def _prompt_step(self, value: str) -> PreparedStep:
        """Return the commit step that writes the resolved prompt into ctx.conv."""

        def apply() -> UndoToken:
            return self._apply_prompt_content(value)

        return PreparedStep(
            service=_CONVERSATION_SERVICE,
            field_paths=("system_prompt",),
            apply=apply,
        )

    def _apply_prompt_content(self, value: str) -> UndoToken:
        """Write the resolved prompt into ctx.conv and return the token that undoes it."""
        ctx = self._ctx
        previous = ctx.conv.system_prompt_content
        ctx.conv.system_prompt_content = value
        return UndoToken(
            service=_CONVERSATION_SERVICE,
            field_paths=("system_prompt",),
            restore=lambda: setattr(ctx.conv, "system_prompt_content", previous),
        )

    def _pending_state(self) -> PendingConfigState | None:
        """Return the container's pending configuration state, if it has one.

        `factory.py` builds one `PendingConfigState` per process and puts it on
        `AppServices`, so the pending records and the degraded guard survive from
        one command to the next (REQ-009, REQ-012).  A ctx without the container
        only loses the cross-command record, not the reload itself.
        """
        return pending_state_for(self._ctx)

    def _refuse_if_degraded(self, pending: PendingConfigState | None) -> None:
        """Raise when a previous reload left a live service inconsistent (REQ-012).

        The service instance carries the record within one command; the container's
        `PendingConfigState` carries it from one command to the next.
        """
        if (
            not self._degraded_services
            and pending is not None
            and not pending.allow_reload()
        ):
            self._degraded_services = pending.degraded_services()
        if self._degraded_services:
            degraded = self._degraded_services
            raise ConfigReloadRollbackError(
                "config reload refused: a previous reload left "
                f"{', '.join(degraded)} inconsistent; restart required",
                service=degraded[0],
                stage=ReloadStage.DEGRADED.value,
            )

    def _record_pending_candidate(
        self,
        pending: PendingConfigState | None,
        startup_only_records: list[PendingChange],
        mcp_records: list[PendingMcpRecord],
    ) -> None:
        """Store the candidate's pending view so the display commands can read it.

        Replace semantics: the stored list is the candidate's complete pending view,
        so a field the next candidate no longer redefines stops being pending
        (REQ-009).
        """
        if pending is None:
            return
        pending.set_mcp_records(mcp_records)
        pending.set_startup_only([record.field_path for record in startup_only_records])

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

    # ── cfg-field update helpers (moved from _ConfigMixin) ────────────────────

    def _detect_diagnostics_live_fields(
        self,
        new_cfg: dict[str, Any],
    ) -> list[str]:
        """Return names of diagnostics.* fields that differ between new_cfg and running cfg.

        These fields take effect immediately on every DiagnosticStore save()/fetch()
        call, independent of /reload — they are config-file-driven, not startup-only.
        """
        return detect_diagnostics_live_fields(self._ctx, new_cfg)


def _mcp_record_display(record: PendingMcpRecord) -> list[str]:
    """Render one MCP definition record as the lines the CLI prints.

    One line per field path the record names, so a changed server prints each
    changed field and an added or removed server prints the server itself.
    """
    suffix = _MCP_RECORD_SUFFIXES.get(record.change, "")
    return [field_path + suffix for field_path in record.field_paths]
