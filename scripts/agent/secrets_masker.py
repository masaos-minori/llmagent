#!/usr/bin/env python3
"""scripts/agent/secrets_masker.py — Mask sensitive values in log output."""

import re

# Single key-name alternation shared by the keyed patterns (diagmask001 Decision 3).
# The composite names are listed explicitly: quoted-JSON keys must match from the key
# start inside the quotes, so suffix alternation alone cannot reach "client_secret".
_KEY_ALT = (
    "password|passwd|pwd|api[_-]?key|apikey|secret|token|access_token|auth_token|"
    "client_secret|bearer|authorization|credential|private_key"
)

SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)((?:password|passwd|pwd)\s*=\s*)(?!>)(\S+)"),
    re.compile(r"(?i)((?:api[_-]?key|apikey)\s*=\s*)(?!>)(\S+)"),
    re.compile(r"(?i)((?:secret|token)\s*=\s*)(?!>)(\S+)"),
    re.compile(r"(?i)(Authorization:\s*\S+\s+)(\S+)"),
    re.compile(r"(?i)(Bearer\s+)(\S+)"),
    re.compile(rf"""(?i)(\"(?:{_KEY_ALT})\"\s*[:,]\s*[\"'])([^\"']+)"""),
    re.compile(
        r"""(?i)((?:password|passwd|pwd|api[_-]?key|apikey|secret|token)\s*:\s*)['"][^'"]*['"]"""
    ),
    re.compile(
        r"(?i)((?:password|passwd|pwd|api[_-]?key|apikey|secret|token)\s*:\s*)(\S+)"
    ),
    re.compile(rf"(?i)((?:{_KEY_ALT})\s*=>\s*)(\S+)"),
    re.compile(
        r"(?i)((?:bearer|authorization|credential|private_key)\s*=\s*)(?!>)(\S+)"
    ),
    re.compile(
        r"(?i)((?:bearer|credential|private_key|access_token|auth_token|client_secret)\s*:\s*)(\S+)"
    ),
    re.compile(r"(?i)((?:authorization)\s*:\s+)(?!(?:Bearer|Basic|Digest)\s)(\S+)"),
    re.compile(
        r"(?i)()(?<![\w.-])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"
    ),
    # The lookbehind starts a match only at the beginning of a scheme-character run;
    # without it every start position rescans the whole run (quadratic on long input).
    re.compile(
        r"(?i)((?<![a-z0-9+.-])[0-9+.-]*[a-z][a-z0-9+.-]*://(?:[^/\s:@]+:)?)"
        r"([^/\s@]+)(?=@)"
    ),
]


def _mask_secrets(text: str) -> str:
    """Mask sensitive values in text using regex patterns."""
    masked = text
    for pattern in SECRET_PATTERNS:
        masked = pattern.sub(lambda m: m.group(1) + "***MASKED***", masked)
    return masked


def detects_secrets(text: str) -> bool:
    """Return True when any SECRET_PATTERNS substitution would change the text."""
    return _mask_secrets(text) != text
