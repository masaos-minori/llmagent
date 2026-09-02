#!/usr/bin/env python3
"""scripts/rag/ingestion/language_resolver.py

LanguageResolver: owns CJK-ratio-based language detection concern.

Extracted from WebCrawler to separate language resolution from BFS orchestration.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Import here to avoid circular imports
from rag.ingestion.crawler_utils import detect_lang  # noqa: E402 — local import for circular dependency avoidance
from rag.utils import MIN_TEXT_LENGTH_FOR_DETECTION  # noqa: E402 — local import for circular dependency avoidance


class LanguageResolver:
    """Owns CJK-ratio-based language detection."""

    def resolve_lang(self, text: str, hint_lang: str) -> str:
        """Determine page language; 'auto' uses CJK-ratio detection with 'en' fallback for short/inconclusive texts; returns a _SUPPORTED_LANGS value."""
        if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
            return "en" if hint_lang == "auto" else hint_lang
        detected = detect_lang(text)
        if hint_lang == "auto":
            return detected or "en"
        return detected if detected is not None else hint_lang
