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
    "loop_guard": {"_ephemeral"},
}

# All ephemeral keys authorized for at least one trusted source, derived from
# TRUSTED_SOURCES so this set cannot drift out of sync with it.
_ALL_EPHEMERAL_KEYS: frozenset[str] = frozenset().union(*TRUSTED_SOURCES.values())

# ── Allowed keys per message role ────────────────────────────────────────────

ROLE_KEY_WHITELIST: dict[str, set[str]] = {
    "system": {"role", "content", "importance", "pinned"},
    "user": {"role", "content", "importance", "pinned"},
    "assistant": {"role", "content", "tool_calls", "importance", "pinned"},
    "tool": {"role", "content", "tool_call_id", "name", "importance", "pinned"},
}


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict


@dataclass(frozen=True)
class ValidationResult:
    """Result of message schema validation."""

    success: bool
    reason: str = ""
mutants_x_validate_message__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate_message__mutmut)
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_orig(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_1(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "XXroleXX" not in msg:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_2(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "ROLE" not in msg:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_3(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" in msg:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_4(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(None, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_5(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, None)
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_6(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult("Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_7(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, )
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_8(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(True, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_9(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "XXMissing 'role' fieldXX")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_10(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_11(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "MISSING 'ROLE' FIELD")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_12(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "XXcontentXX" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_13(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "CONTENT" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_14(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_15(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(None, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_16(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, None)

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_17(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult("Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_18(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, )

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_19(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(True, "Missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_20(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "XXMissing 'content' fieldXX")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_21(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "missing 'content' field")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_22(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "MISSING 'CONTENT' FIELD")

    role = msg["role"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_23(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = None
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_24(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["XXroleXX"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_25(msg: dict) -> ValidationResult:
    """Validate *msg* against the strict schema.

    Required fields: ``role``, ``content``.
    Optional fields must be in the allowed whitelist for that role.
    Ephemeral keys are only allowed when the message carries a trusted ``source`` field.
    """
    if "role" not in msg:
        return ValidationResult(False, "Missing 'role' field")
    if "content" not in msg:
        return ValidationResult(False, "Missing 'content' field")

    role = msg["ROLE"]
    if role not in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_26(msg: dict) -> ValidationResult:
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
    if role in ROLE_KEY_WHITELIST:
        return ValidationResult(False, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_27(msg: dict) -> ValidationResult:
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
        return ValidationResult(None, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_28(msg: dict) -> ValidationResult:
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
        return ValidationResult(False, None)

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_29(msg: dict) -> ValidationResult:
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
        return ValidationResult(f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_30(msg: dict) -> ValidationResult:
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
        return ValidationResult(False, )

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_31(msg: dict) -> ValidationResult:
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
        return ValidationResult(True, f"Unknown role: {role}")

    allowed_keys = ROLE_KEY_WHITELIST[role]
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_32(msg: dict) -> ValidationResult:
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

    allowed_keys = None
    extra_keys = set(msg.keys()) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_33(msg: dict) -> ValidationResult:
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
    extra_keys = None
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_34(msg: dict) -> ValidationResult:
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
    extra_keys = set(msg.keys()) + allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_35(msg: dict) -> ValidationResult:
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
    extra_keys = set(None) - allowed_keys
    if extra_keys:
        # Check if extra keys are ephemeral keys injected by an untrusted source
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_36(msg: dict) -> ValidationResult:
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
        ephemeral_keys = None
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


def x_validate_message__mutmut_37(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys | _ALL_EPHEMERAL_KEYS
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


def x_validate_message__mutmut_38(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = None
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


def x_validate_message__mutmut_39(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get(None, "")
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


def x_validate_message__mutmut_40(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", None)
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


def x_validate_message__mutmut_41(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("")
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


def x_validate_message__mutmut_42(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", )
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


def x_validate_message__mutmut_43(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("XXsourceXX", "")
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


def x_validate_message__mutmut_44(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("SOURCE", "")
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


def x_validate_message__mutmut_45(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "XXXX")
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


def x_validate_message__mutmut_46(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source in TRUSTED_SOURCES:
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


def x_validate_message__mutmut_47(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
                    None,
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


def x_validate_message__mutmut_48(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
                    False,
                    None,
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


def x_validate_message__mutmut_49(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
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


def x_validate_message__mutmut_50(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
                    False,
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


def x_validate_message__mutmut_51(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
                    True,
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


def x_validate_message__mutmut_52(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
                    False,
                    f"Ephemeral keys not allowed for source '{source}': {ephemeral_keys}",
                )
            allowed_ephemeral = None
            unauthorized = ephemeral_keys - allowed_ephemeral
            if unauthorized:
                return ValidationResult(
                    False,
                    f"Unauthorized ephemeral keys for source '{source}': {unauthorized}",
                )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_53(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
                    False,
                    f"Ephemeral keys not allowed for source '{source}': {ephemeral_keys}",
                )
            allowed_ephemeral = TRUSTED_SOURCES[source]
            unauthorized = None
            if unauthorized:
                return ValidationResult(
                    False,
                    f"Unauthorized ephemeral keys for source '{source}': {unauthorized}",
                )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_54(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
        if ephemeral_keys:
            source = msg.get("source", "")
            if source not in TRUSTED_SOURCES:
                return ValidationResult(
                    False,
                    f"Ephemeral keys not allowed for source '{source}': {ephemeral_keys}",
                )
            allowed_ephemeral = TRUSTED_SOURCES[source]
            unauthorized = ephemeral_keys + allowed_ephemeral
            if unauthorized:
                return ValidationResult(
                    False,
                    f"Unauthorized ephemeral keys for source '{source}': {unauthorized}",
                )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_55(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
                    None,
                    f"Unauthorized ephemeral keys for source '{source}': {unauthorized}",
                )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_56(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
                    None,
                )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_57(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
                    f"Unauthorized ephemeral keys for source '{source}': {unauthorized}",
                )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_58(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
                    )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_59(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
                    True,
                    f"Unauthorized ephemeral keys for source '{source}': {unauthorized}",
                )
        else:
            return ValidationResult(False, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_60(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
            return ValidationResult(None, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_61(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
            return ValidationResult(False, None)

    return ValidationResult(True)


def x_validate_message__mutmut_62(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
            return ValidationResult(f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_63(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
            return ValidationResult(False, )

    return ValidationResult(True)


def x_validate_message__mutmut_64(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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
            return ValidationResult(True, f"Unexpected keys: {extra_keys}")

    return ValidationResult(True)


def x_validate_message__mutmut_65(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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

    return ValidationResult(None)


def x_validate_message__mutmut_66(msg: dict) -> ValidationResult:
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
        ephemeral_keys = extra_keys & _ALL_EPHEMERAL_KEYS
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

    return ValidationResult(False)

mutants_x_validate_message__mutmut['_mutmut_orig'] = x_validate_message__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_1'] = x_validate_message__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_2'] = x_validate_message__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_3'] = x_validate_message__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_4'] = x_validate_message__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_5'] = x_validate_message__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_6'] = x_validate_message__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_7'] = x_validate_message__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_8'] = x_validate_message__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_9'] = x_validate_message__mutmut_9 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_10'] = x_validate_message__mutmut_10 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_11'] = x_validate_message__mutmut_11 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_12'] = x_validate_message__mutmut_12 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_13'] = x_validate_message__mutmut_13 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_14'] = x_validate_message__mutmut_14 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_15'] = x_validate_message__mutmut_15 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_16'] = x_validate_message__mutmut_16 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_17'] = x_validate_message__mutmut_17 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_18'] = x_validate_message__mutmut_18 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_19'] = x_validate_message__mutmut_19 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_20'] = x_validate_message__mutmut_20 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_21'] = x_validate_message__mutmut_21 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_22'] = x_validate_message__mutmut_22 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_23'] = x_validate_message__mutmut_23 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_24'] = x_validate_message__mutmut_24 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_25'] = x_validate_message__mutmut_25 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_26'] = x_validate_message__mutmut_26 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_27'] = x_validate_message__mutmut_27 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_28'] = x_validate_message__mutmut_28 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_29'] = x_validate_message__mutmut_29 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_30'] = x_validate_message__mutmut_30 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_31'] = x_validate_message__mutmut_31 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_32'] = x_validate_message__mutmut_32 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_33'] = x_validate_message__mutmut_33 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_34'] = x_validate_message__mutmut_34 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_35'] = x_validate_message__mutmut_35 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_36'] = x_validate_message__mutmut_36 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_37'] = x_validate_message__mutmut_37 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_38'] = x_validate_message__mutmut_38 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_39'] = x_validate_message__mutmut_39 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_40'] = x_validate_message__mutmut_40 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_41'] = x_validate_message__mutmut_41 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_42'] = x_validate_message__mutmut_42 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_43'] = x_validate_message__mutmut_43 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_44'] = x_validate_message__mutmut_44 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_45'] = x_validate_message__mutmut_45 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_46'] = x_validate_message__mutmut_46 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_47'] = x_validate_message__mutmut_47 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_48'] = x_validate_message__mutmut_48 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_49'] = x_validate_message__mutmut_49 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_50'] = x_validate_message__mutmut_50 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_51'] = x_validate_message__mutmut_51 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_52'] = x_validate_message__mutmut_52 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_53'] = x_validate_message__mutmut_53 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_54'] = x_validate_message__mutmut_54 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_55'] = x_validate_message__mutmut_55 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_56'] = x_validate_message__mutmut_56 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_57'] = x_validate_message__mutmut_57 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_58'] = x_validate_message__mutmut_58 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_59'] = x_validate_message__mutmut_59 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_60'] = x_validate_message__mutmut_60 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_61'] = x_validate_message__mutmut_61 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_62'] = x_validate_message__mutmut_62 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_63'] = x_validate_message__mutmut_63 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_64'] = x_validate_message__mutmut_64 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_65'] = x_validate_message__mutmut_65 # type: ignore # mutmut generated
mutants_x_validate_message__mutmut['x_validate_message__mutmut_66'] = x_validate_message__mutmut_66 # type: ignore # mutmut generated
mutants_x_is_trusted_source__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_is_trusted_source__mutmut)
def is_trusted_source(source_id: str) -> bool:
    """Check if *source_id* is authorized to inject ephemeral keys."""
    return source_id in TRUSTED_SOURCES


def x_is_trusted_source__mutmut_orig(source_id: str) -> bool:
    """Check if *source_id* is authorized to inject ephemeral keys."""
    return source_id in TRUSTED_SOURCES


def x_is_trusted_source__mutmut_1(source_id: str) -> bool:
    """Check if *source_id* is authorized to inject ephemeral keys."""
    return source_id not in TRUSTED_SOURCES

mutants_x_is_trusted_source__mutmut['_mutmut_orig'] = x_is_trusted_source__mutmut_orig # type: ignore # mutmut generated
mutants_x_is_trusted_source__mutmut['x_is_trusted_source__mutmut_1'] = x_is_trusted_source__mutmut_1 # type: ignore # mutmut generated
mutants_x_get_allowed_ephemeral_keys__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_get_allowed_ephemeral_keys__mutmut)
def get_allowed_ephemeral_keys(source_id: str) -> set[str]:
    """Get ephemeral keys allowed for a trusted source."""
    if source_id in TRUSTED_SOURCES:
        return TRUSTED_SOURCES[source_id]
    return set()


def x_get_allowed_ephemeral_keys__mutmut_orig(source_id: str) -> set[str]:
    """Get ephemeral keys allowed for a trusted source."""
    if source_id in TRUSTED_SOURCES:
        return TRUSTED_SOURCES[source_id]
    return set()


def x_get_allowed_ephemeral_keys__mutmut_1(source_id: str) -> set[str]:
    """Get ephemeral keys allowed for a trusted source."""
    if source_id not in TRUSTED_SOURCES:
        return TRUSTED_SOURCES[source_id]
    return set()

mutants_x_get_allowed_ephemeral_keys__mutmut['_mutmut_orig'] = x_get_allowed_ephemeral_keys__mutmut_orig # type: ignore # mutmut generated
mutants_x_get_allowed_ephemeral_keys__mutmut['x_get_allowed_ephemeral_keys__mutmut_1'] = x_get_allowed_ephemeral_keys__mutmut_1 # type: ignore # mutmut generated
