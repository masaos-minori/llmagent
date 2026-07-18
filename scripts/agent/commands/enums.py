"""agent/commands/enums.py

Domain enums for built-in slash-command handlers.
"""

from __future__ import annotations

from enum import StrEnum


class CommandKind(StrEnum):
    """Categories of slash commands available in the agent REPL."""

    MEMORY = "memory"
    SESSION = "session"
    CONTEXT = "context"
    DB = "db"
    DEBUG = "debug"
    MCP = "mcp"
    TOOLING = "tooling"
    CONFIG = "config"


class MemoryAction(StrEnum):
    """Actions available under the /memory command group."""

    LIST = "list"
    SEARCH = "search"
    SHOW = "show"
    ADD = "add"
    DELETE = "delete"
    PIN = "pin"
    UNPIN = "unpin"
    PRUNE = "prune"


class DbAction(StrEnum):
    """Actions available under the /db command group."""

    STATS = "stats"
    HEALTH = "health"
    CHECKPOINT = "checkpoint"
    VACUUM = "vacuum"
    PURGE = "purge"
    RECOVER = "recover"
    LIST = "list"


class McpAction(StrEnum):
    """Actions available under the /mcp command group."""

    STATUS = "status"
    PROBE = "probe"


class SessionAction(StrEnum):
    """Actions available under the /session command group."""

    LIST = "list"
    LOAD = "load"
    RENAME = "rename"
    DELETE = "delete"
