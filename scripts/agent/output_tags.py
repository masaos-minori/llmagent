"""agent/output_tags.py

Canonical bracket-prefix tags for REPL/CLI status messages (warnings, errors,
tool-execution status, workflow status). Centralizes tags previously
hardcoded as string literals per call site, which had drifted into
inconsistent casing (e.g. `[fatal]` vs `[FATAL]`).
"""

from __future__ import annotations

from enum import StrEnum


class OutputTag(StrEnum):
    """Bracketed prefix tags for REPL/CLI status messages."""

    WARN = "[warn]"
    FATAL = "[fatal]"
    NON_FATAL = "[non-fatal]"
    ERROR = "[error]"
    USAGE = "[usage]"
    TOOL = "[tool]"
    APPROVAL = "[approval]"
    APPROVAL_PENDING = "[approval-pending]"
    DENIED = "[denied]"
    PLAN_BLOCKED = "[plan-blocked]"
    SKIPPED = "[skipped]"
    CONTEXT = "[context]"
    RAG = "[rag]"
    WORKFLOW = "[workflow]"
