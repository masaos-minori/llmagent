"""agent/commands/enums.py
Domain enums for built-in slash-command handlers.
"""

from __future__ import annotations

from enum import StrEnum


class CommandKind(StrEnum):
    MEMORY = "memory"
    SESSION = "session"
    CONTEXT = "context"
    DB = "db"
    DEBUG = "debug"
    MCP = "mcp"
    TOOLING = "tooling"
    CONFIG = "config"


class MemoryAction(StrEnum):
    LIST = "list"
    SEARCH = "search"
    SHOW = "show"
    ADD = "add"
    DELETE = "delete"
    PIN = "pin"
    UNPIN = "unpin"
    PRUNE = "prune"


class DbAction(StrEnum):
    STATS = "stats"
    HEALTH = "health"
    CHECKPOINT = "checkpoint"
    VACUUM = "vacuum"
    PURGE = "purge"
    RECOVER = "recover"
    LIST = "list"


class McpAction(StrEnum):
    STATUS = "status"
    INSTALL = "install"
    PROBE = "probe"


class SessionAction(StrEnum):
    LIST = "list"
    LOAD = "load"
    RENAME = "rename"
    DELETE = "delete"
