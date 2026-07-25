"""scripts/agent/message_schema.py — Schema validation for conversation history messages.

Prevents LLM from manipulating ephemeral message filtering by injecting/removing
keys like ``_ephemeral``, ``_memory_injected``, or ``_skill_ephemeral``.

Ephemeral key injection is restricted to trusted sources only (command handlers).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Trusted sources authorized to inject ephemeral keys ──────────────────────

TRUSTED_SOURCES: dict[str, set[str]] = {
    "cmd_handler": {"_ephemeral"},
    "memory_injection": {"_memory_injected"},
    "skill_mixin": {"_skill_ephemeral"},
}

# ── Allowed keys per message role ────────────────────────────────────────────

ROLE_KEY_WHITELIST: dict[str, set[str]] = {
    "system": {"role", "content", "priority"},
    "user": {"role", "content"},
    "assistant": {"role", "content", "tool_calls"},
    "tool": {"role", "content", "tool_call_id"},
}


@dataclass(frozen=True)
class ValidationResult:
    """Result of message schema validation."""

    success: bool
    reason: str = ""


def validate_message(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & {
            "_ephemeral",
            "_memory_injected",
            "_skill_ephemeral",
        }
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
                    False,
                    f"Ephemeral keys not allowed for source '{source}': {ephemeral_keys}",
                )
            allowed_ephemeral = TRUSTED_SOURCES[source]
            unauthorized = ephemeral_keys - allowed_ephemeral
            if unauthorized:
                return ValidationResult(
                    False,
                    f"Unauthorized ephemeral keys for source '{source}': {unauthorized}",
                )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def is_trusted_source(source_id: str) -> bool:
    """Check if *source_id* is authorized to inject ephemeral keys."""
    return source_id in TRUSTED_SOURCES


def get_allowed_ephemeral_keys(source_id: str) -> set[str]:
    """Get ephemeral keys allowed for a trusted source."""
    if source_id in TRUSTED_SOURCES:
        return TRUSTED_SOURCES[source_id]
    return set()
