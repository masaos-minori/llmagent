#!/usr/bin/env python3
"""shared/events.py
Typed event definitions for agent lifecycle and artifact notifications.

ArtifactEvent is a pure data definition — no event bus yet.
"""

from __future__ import annotations

from typing import TypedDict


class ArtifactEvent(TypedDict, total=False):
    """Emitted when a repo artifact is created or updated."""

    event_type: str  # "artifact.updated" | "artifact.created" | "artifact.deleted"
    repo: str  # "owner/repo"
    branch: str  # branch name
    commit: str  # commit SHA or empty
    path: str  # file path or empty (for whole-branch events)
    pr_number: int  # PR number or 0
    session_id: int  # agent session that triggered the event
    timestamp: str  # ISO-8601 UTC
