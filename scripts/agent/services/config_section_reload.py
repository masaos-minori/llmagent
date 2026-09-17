"""Section reload logic — validated (llm/rag/tool) and direct (approval/memory/mcp) paths."""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from agent.context import AgentContext

from agent.services.config_field_registry import registry_for
from agent.services.exceptions import ConfigReloadValidationError


def reload_validated_section(
    ctx: AgentContext,
    section_path: str,
    new_cfg: dict[str, Any],
) -> list[str]:
    """Reload a validated section (llm/rag/tool) using dataclasses.replace + validators.

    Args:
        ctx: AgentContext with cfg attribute.
        section_path: Section identifier (e.g., "llm", "rag", "tool").
        new_cfg: New configuration dictionary.

    Returns:
        List of applied section names.
    """
    cfg = getattr(ctx.cfg, section_path)
    changed_fields: dict[str, Any] = {}

    for field_entry in registry_for(section_path):
        value = new_cfg.get(field_entry.name)
        if value is None or value == getattr(cfg, field_entry.name):
            continue
        changed_fields[field_entry.name] = value

    if not changed_fields:
        return []

    try:
        replaced = dataclasses.replace(cfg, **changed_fields)
    except ValueError as e:
        raise ConfigReloadValidationError(str(e)) from e

    for field_entry in registry_for(section_path):
        if field_entry.name in changed_fields:
            validator = field_entry.validator_fn
            if validator is not None:
                validator(replaced)

    setattr(ctx.cfg, section_path, replaced)
    return [section_path]


def reload_direct_fields(
    ctx: AgentContext,
    new_cfg: dict[str, Any],
    section_path: str,
    field_filter: set[str] | None = None,
) -> dict[str, Any]:
    """Reload a direct section (approval/memory/mcp) using setattr.

    Args:
        ctx: AgentContext with cfg attribute.
        new_cfg: New configuration dictionary.
        section_path: Section identifier (e.g., "approval", "memory", "mcp").
        field_filter: Optional set of field names to process; processes all if None.

    Returns:
        Dict of changed fields.
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

    if not changed_fields:
        return {}

    for field_name, value in changed_fields.items():
        setattr(cfg, field_name, value)

    return changed_fields
