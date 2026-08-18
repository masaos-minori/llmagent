"""Audit logging integration."""

import logging

logger = logging.getLogger("security.audit")


class AuditLogger:
    """Centralized audit logging for security events."""

    @staticmethod
    def log_security_event(event_type: str, details: dict) -> None:
        """Log a security event."""
        logger.warning(
            "SECURITY_EVENT type=%s details=%s",
            event_type,
            details,
        )
