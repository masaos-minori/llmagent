#!/usr/bin/env python3
"""scripts/agent/secrets_masker.py — Mask sensitive values in log output."""

import re

SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(password|passwd|pwd)\s*=\s*\S+"),
    re.compile(r"(?i)(api[_-]?key|apikey)\s*=\s*\S+"),
    re.compile(r"(?i)(secret|token)\s*=\s*\S+"),
]


def _mask_secrets(text: str) -> str:
    """Mask sensitive values in text using regex patterns."""
    masked = text
    for pattern in SECRET_PATTERNS:
        masked = pattern.sub(lambda m: m.group()[:10] + "***MASKED***", masked)
    return masked
