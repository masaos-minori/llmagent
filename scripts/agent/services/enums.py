"""agent/services/enums.py

Enum types for the agent/services subsystem.
"""

from __future__ import annotations

from enum import StrEnum


class McpTier(StrEnum):
    """Security tier classification for MCP servers."""

    READ_ONLY = "READ_ONLY"
    WRITE_SAFE = "WRITE_SAFE"
    WRITE_DANGEROUS = "WRITE_DANGEROUS"
    ADMIN = "ADMIN"


class McpAvailability(StrEnum):
    """Runtime availability state of an MCP server."""

    OK = "OK"
    STOPPED = "STOPPED"
    NOT_STARTED = "NOT_STARTED"
    DEAD = "DEAD"
    NO_URL = "no-url"
    HTTP_ERROR = "http_error"
    FAIL = "fail"
    UNKNOWN = "unknown"


class ConversationActionType(StrEnum):
    """Types of conversation-level actions that can be performed."""

    CLEAR = "clear"
    SWITCH_PROMPT = "switch_prompt"


class ExportFormat(StrEnum):
    """Supported export formats for agent session data."""

    JSON = "json"
    MARKDOWN = "markdown"
