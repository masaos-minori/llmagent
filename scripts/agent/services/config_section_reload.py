"""scripts/agent/services/config_section_reload.py — Section reload logic split into prepare (candidate build + validators / changed-field collection, no live mutation) and apply (setattr only) halves for the validated (llm/rag/tool) and direct (approval/memory/mcp) paths."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.context import AgentContext

from agent.services.config_field_registry import registry_for
from agent.services.exceptions import ConfigReloadValidationError


def prepare_validated_section(
    ctx: AgentContext,
    section_path: str,
    new_cfg: dict[str, Any],
    extra_changed_fields: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], Any]:
    """Build the dataclasses.replace candidate for a validated section (llm/rag/tool) and run its validators.

    Performs no live mutation: the candidate is returned unapplied so callers
    can validate the whole config before committing.

    Args:
        ctx: AgentContext with cfg attribute.
        section_path: Section identifier (e.g., "llm", "rag", "tool").
        new_cfg: New configuration dictionary.
        extra_changed_fields: Optional fields merged into the changed set before
            candidate construction (e.g. masked_fields, which is not a registry
            entry); used to fold direct updates into the section candidate.

    Returns:
        Tuple (changed_fields, candidate). ({}, None) when nothing changed.

    Raises:
        ConfigReloadValidationError: On any validator failure.
    """
    cfg = getattr(ctx.cfg, section_path)
    changed_fields: dict[str, Any] = {}

    for field_entry in registry_for(section_path):
        value = new_cfg.get(field_entry.name)
        if value is None or value == getattr(cfg, field_entry.name):
            continue
        changed_fields[field_entry.name] = value

    if extra_changed_fields:
        changed_fields.update(extra_changed_fields)

    if not changed_fields:
        return {}, None

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

    return changed_fields, replaced


def apply_validated_section(
    ctx: AgentContext,
    section_path: str,
    candidate: Any,
) -> None:
    """Commit a prepared validated-section candidate onto ctx.cfg.

    Args:
        ctx: AgentContext with cfg attribute.
        section_path: Section identifier (e.g., "llm", "rag", "tool").
        candidate: Prepared section candidate from prepare_validated_section.
    """
    setattr(ctx.cfg, section_path, candidate)


def reload_validated_section(
    ctx: AgentContext,
    section_path: str,
    new_cfg: dict[str, Any],
) -> list[str]:
    """Reload a validated section (llm/rag/tool) as a prepare-then-apply composition.

    Args:
        ctx: AgentContext with cfg attribute.
        section_path: Section identifier (e.g., "llm", "rag", "tool").
        new_cfg: New configuration dictionary.

    Returns:
        List of applied section names.
    """
    changed_fields, candidate = prepare_validated_section(ctx, section_path, new_cfg)
    if not changed_fields:
        return []
    apply_validated_section(ctx, section_path, candidate)
    return [section_path]


def prepare_direct_section(
    ctx: AgentContext,
    new_cfg: dict[str, Any],
    section_path: str,
    field_filter: set[str] | None = None,
) -> dict[str, Any]:
    """Collect changed fields for a direct section (approval/memory/mcp).

    No validators run and no candidate is built: direct sections carry no
    registry validators, and their live objects are not guaranteed to be
    dataclasses (test fixtures model them as mocks). Performs no mutation.

    Args:
        ctx: AgentContext with cfg attribute.
        new_cfg: New configuration dictionary.
        section_path: Section identifier (e.g., "approval", "memory", "mcp").
        field_filter: Optional set of field names to process; processes all if None.

    Returns:
        Dict of changed fields (empty when nothing changed).
    """
    cfg = getattr(ctx.cfg, section_path)
    changed_fields: dict[str, Any] = {}

    for field_entry in registry_for(section_path):
        if field_filter is not None and field_entry.name not in field_filter:
            continue
        value = new_cfg.get(field_entry.name)
        if value is None or value == getattr(cfg, field_entry.name):
            continue
        changed_fields[field_entry.name] = value

    return changed_fields


def apply_direct_section(
    ctx: AgentContext,
    section_path: str,
    changed_fields: dict[str, Any],
) -> None:
    """Commit prepared direct-section changes onto the live section object.

    Args:
        ctx: AgentContext with cfg attribute.
        section_path: Section identifier (e.g., "approval", "memory", "mcp").
        changed_fields: Changed fields collected by prepare_direct_section.
    """
    cfg = getattr(ctx.cfg, section_path)
    for field_name, value in changed_fields.items():
        setattr(cfg, field_name, value)


def reload_direct_fields(
    ctx: AgentContext,
    new_cfg: dict[str, Any],
    section_path: str,
    field_filter: set[str] | None = None,
) -> dict[str, Any]:
    """Reload a direct section (approval/memory/mcp) as a prepare-then-apply composition.

    Args:
        ctx: AgentContext with cfg attribute.
        new_cfg: New configuration dictionary.
        section_path: Section identifier (e.g., "approval", "memory", "mcp").
        field_filter: Optional set of field names to process; processes all if None.

    Returns:
        Dict of changed fields.
    """
    changed_fields = prepare_direct_section(ctx, new_cfg, section_path, field_filter)
    if not changed_fields:
        return {}
    apply_direct_section(ctx, section_path, changed_fields)
    return changed_fields
