#!/usr/bin/env python3
"""agent/lifecycle.py
LifecycleState enum shared by lifecycle managers and callers.

ServerLifecycleManager facade has been removed — routing is now handled
by _ServerLifecycleRouter in factory.py.
"""

from __future__ import annotations

from enum import Enum


class LifecycleState(Enum):
    """Unified transport state for all server types (HTTP and stdio)."""

    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    UNKNOWN = "unknown"
