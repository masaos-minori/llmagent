"""
example.py — Plugin example / template.

Copy this file and rename it (e.g. my_plugin.py) to create a new plugin.
Each @register_* decorator runs at import time when load_plugins() loads the file.

To activate: place the file in plugins/ and restart the agent.
To deactivate: remove or rename the file (e.g. example.py.disabled).
"""

from shared.plugin_registry import (
    register_command,
    register_pipeline_stage,
    register_tool,
)

# ── Feature flags ─────────────────────────────────────────────────────────────
# Set to True to activate post-rerank score filtering.
ENABLE_SCORE_FILTER = False

# ── Slash command: /ping ──────────────────────────────────────────────────────


@register_command("/ping")
async def cmd_ping(ctx: object, args: str) -> None:
    """Reply with pong.  Usage: /ping"""
    print("pong")


# ── Local tool: echo ──────────────────────────────────────────────────────────


@register_tool("echo")
async def tool_echo(args: dict) -> tuple[str, bool]:
    """Return the 'text' argument as-is.  Useful for testing tool routing."""
    text = str(args.get("text", ""))
    return text, False


# ── Pipeline post-stage: score filter ────────────────────────────────────────


@register_pipeline_stage(when="post")
async def stage_score_filter(hits: list, query: str) -> list:
    """Drop hits with score below 0.05.

    Disabled by default (ENABLE_SCORE_FILTER = False).
    Set ENABLE_SCORE_FILTER = True to activate.
    """
    if not ENABLE_SCORE_FILTER:
        return hits
    return [h for h in hits if h.get("score", 1.0) >= 0.05]
