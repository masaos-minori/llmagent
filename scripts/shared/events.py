#!/usr/bin/env python3
"""shared/events.py
Typed event definitions for agent lifecycle and artifact notifications.

ArtifactEvent is a pure data structure (TypedDict). It has no delivery system,
no event bus, and no consumers. It exists solely as a type annotation for code
that may emit artifact events in the future. Do not assume that creating an
ArtifactEvent instance triggers any action.

Future event-envelope fields (aspirational, not implemented):
    event_id: str        # UUID v7
    source: str          # module name (e.g. "mcp/github")
    timestamp: str       # ISO-8601 UTC (already present)
    correlation_id: str  # trace ID linking related events
These fields are documented here as design direction only; they are not required
and must not be assumed to exist on any event instance.
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
