#!/usr/bin/env python3
"""scripts/agent/memory/config_path.py — Shared resolver for the memory JSONL archive directory.

Returns the flat ``memory_jsonl_dir`` config path via the builder's default so the
three change-event writers append to the archive instead of raising
``KeyError('memory')`` from the nonexistent nested
``cfg["memory"]["memory_jsonl_dir"]`` shape.
"""


def resolve_memory_jsonl_dir() -> str:
    """Return the flat ``memory_jsonl_dir`` path using the builder default.

    Reads the raw flat TOML dict and resolves the key through the same
    ``_get_str_or_default`` helper that ``_build_memory_config`` uses, so the
    returned value equals ``ctx.cfg.memory.memory_jsonl_dir`` for the same input.
    """
    from shared.config_loader import ConfigLoader

    from agent.config_section_builders import _get_str_or_default

    cfg = ConfigLoader().load("agent.toml")
    return _get_str_or_default(cfg, "memory_jsonl_dir", "/opt/llm/memory")
