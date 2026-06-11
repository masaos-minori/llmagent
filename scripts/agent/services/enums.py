"""agent/services/enums.py
Enum types for the agent/services subsystem.
"""

from __future__ import annotations

from enum import StrEnum


class IngestStage(StrEnum):
    OK = "ok"
    CRAWL = "crawl"
    SPLIT = "split"
    INGEST = "ingest"


class McpTier(StrEnum):
    READ_ONLY = "READ_ONLY"
    WRITE_SAFE = "WRITE_SAFE"
    WRITE_DANGEROUS = "WRITE_DANGEROUS"
    ADMIN = "ADMIN"


class McpAvailability(StrEnum):
    OK = "OK"
    STOPPED = "STOPPED"
    NOT_STARTED = "NOT_STARTED"
    DEAD = "DEAD"
    NO_URL = "no-url"
    HTTP_ERROR = "http_error"
    FAIL = "fail"


class ConversationActionType(StrEnum):
    CLEAR = "clear"
    SWITCH_PROMPT = "switch_prompt"


class ExportFormat(StrEnum):
    JSON = "json"
    MARKDOWN = "markdown"
