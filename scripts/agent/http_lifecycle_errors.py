"""scripts/agent/http_lifecycle_errors.py

Exceptions and dataclasses for HTTP subprocess MCP server startup failures.

Extracted from http_lifecycle.py to break circular imports between
http_lifecycle.py and http_lifecycle_command_validator.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from agent.secrets_masker import _mask_secrets

logger = logging.getLogger(__name__)

@dataclass
class StartupFailure:
    """Records the full stderr output and reason when an HTTP subprocess fails to start."""

    server_key: str
    reason: str
    stderr_full: str

class HttpStartupError(RuntimeError):
    """Raised when an HTTP subprocess MCP server fails to start."""

    def __init__(self, failure: StartupFailure) -> None:
        """Initialize with the startup failure details."""
        self.failure = failure
        super().__init__(failure.reason)

    def __str__(self) -> str:
        """Return a human-readable representation including all failure details."""
        parts = [f"{self.failure.server_key}: {self.failure.reason}"]
        if self.failure.stderr_full:
            tail = self.failure.stderr_full[-65536:]
            if _mask_secrets is not None:
                masked = _mask_secrets(tail)
            else:
                masked = tail
            parts.append(f"(stderr_tail: {masked})")
        return "\n".join(parts)
