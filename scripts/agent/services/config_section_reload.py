"""scripts/agent/services/config_section_reload.py — Section reload logic split into prepare (typed candidate build + validators, no live mutation) and apply (setattr only) halves for the validated (llm/tool/memory/approval) sections."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.context import AgentContext

from shared.config_field_types import ConfigFieldTypeError, apply_field_rule
from shared.config_undo import UndoToken

from agent.services.config_field_registry import registry_for
from agent.services.exceptions import ConfigReloadValidationError


@dataclasses.dataclass(frozen=True)
class SectionCandidate:
    """A prepared, validated candidate for one configuration section.

    Carries the field paths it changes so an error or a report can name the field
    without the value (REQ-011).

    Attributes:
        section_path: Section identifier (e.g. "llm", "tool", "memory", "approval").
        field_paths: Dotted ``section.field`` paths of the fields the candidate changes.
        section: Typed section object built from the live section by the shared
            type rules.
    """

    section_path: str
    field_paths: tuple[str, ...]
    section: Any


def prepare_validated_section(
    ctx: AgentContext,
    section_path: str,
    candidate_section: Any,
    extra_changed_fields: dict[str, Any] | None = None,
) -> SectionCandidate | None:
    """Diff one hot-reloadable section of the typed candidate against the live section and run its validators.

    Performs no live mutation: the candidate is returned unapplied so callers
    can validate the whole config before committing. Only hot-reloadable registry
    entries are collected, so a startup-only field never enters a candidate
    (REQ-003), and a value the payload does not name is identical on both sides
    because the candidate was built from the live configuration (REQ-002).

    Args:
        ctx: AgentContext with cfg attribute.
        section_path: Section identifier (e.g., "llm", "tool", "memory", "approval").
        candidate_section: The typed section built by `build_agent_config(cfg_override=...)`.
        extra_changed_fields: Optional fields merged into the changed set before
            candidate construction (e.g. masked_fields, which is not a registry
            entry); used to fold direct updates into the section candidate.

    Returns:
        SectionCandidate, or None when nothing changed.

    Raises:
        ConfigReloadValidationError: On any validator failure.
    """
    cfg = getattr(ctx.cfg, section_path)
    changed_fields: dict[str, Any] = {}

    for field_entry in registry_for(section_path):
        value = getattr(candidate_section, field_entry.name)
        # The declared rule is applied to the candidate value as well: the shared
        # builders already enforce the type, and this is where the registry's
        # allow_empty decision is enforced for a field the payload supplies.
        if field_entry.field_type is not None:
            try:
                value = apply_field_rule(
                    field_entry.field_type,
                    value,
                    field_entry.name,
                    allow_empty=field_entry.allow_empty,
                )
            except ConfigFieldTypeError as exc:
                raise ConfigReloadValidationError(str(exc)) from exc
        if value == getattr(cfg, field_entry.name):
            continue
        changed_fields[field_entry.name] = value

    if extra_changed_fields:
        changed_fields.update(extra_changed_fields)

    if not changed_fields:
        return None

    try:
        replaced = dataclasses.replace(cfg, **changed_fields)
    except ValueError as e:
        raise ConfigReloadValidationError(str(e)) from e

    for field_entry in registry_for(section_path):
        if field_entry.name in changed_fields:
            validator = field_entry.validator_fn
            if validator is not None:
                try:
                    validator(replaced)
                except ValueError as e:
                    raise ConfigReloadValidationError(str(e)) from e

    return SectionCandidate(
        section_path=section_path,
        field_paths=tuple(f"{section_path}.{name}" for name in sorted(changed_fields)),
        section=replaced,
    )


def apply_validated_section(
    ctx: AgentContext,
    candidate: SectionCandidate,
) -> UndoToken:
    """Commit a prepared validated-section candidate onto ctx.cfg.

    The section object the candidate replaces is captured first, so the returned
    token writes the previous section back into the same `ctx.cfg` — the live
    services hold that instance, and a rollback must not replace it (REQ-006).

    Args:
        ctx: AgentContext with cfg attribute.
        candidate: Prepared section candidate from prepare_validated_section.

    Returns:
        UndoToken that restores the section this call replaced.
    """
    previous = getattr(ctx.cfg, candidate.section_path)
    setattr(ctx.cfg, candidate.section_path, candidate.section)
    return UndoToken(
        service=candidate.section_path,
        field_paths=candidate.field_paths,
        restore=lambda: setattr(ctx.cfg, candidate.section_path, previous),
    )
