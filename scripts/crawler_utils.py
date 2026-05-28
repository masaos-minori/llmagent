#!/usr/bin/env python3
"""
crawler_utils.py
Pure-function utilities for WebCrawler: URL helpers, content extraction,
language detection, and target URL parsing.

Extracted from web_crawler.py to keep WebCrawler under 400 lines.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urldefrag, urlparse

import trafilatura
from bs4 import BeautifulSoup
from rag_utils import validate_url

# Supported language codes for resolved (output) lang values
_SUPPORTED_LANGS: frozenset[str] = frozenset({"en", "ja"})
# Valid hint lang values including "auto" for per-page CJK-ratio detection
_VALID_HINT_LANGS: frozenset[str] = frozenset({"en", "ja", "auto"})
# CJK character ratio threshold above which text is classified as Japanese
_CJK_RATIO_THRESHOLD: float = 0.1


def url_to_slug(url: str) -> str:
    """Convert a URL to a filesystem-safe ASCII slug (max 80 chars).

    Strips scheme, replaces non-alphanumeric chars with hyphens.
    Example: https://ziglang.org/documentation/ -> ziglang.org-documentation
    """
    slug = re.sub(r"^https?://", "", url)
    slug = re.sub(r"[^a-zA-Z0-9._-]", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:80]


def normalize_url(url: str) -> str:
    """Normalize a URL by stripping the fragment and trailing slash."""
    url, _ = urldefrag(url)
    return url.rstrip("/")


def same_origin(url: str, base: str) -> bool:
    """Return True if url and base share the same origin (scheme + hostname)."""
    p1, p2 = urlparse(url), urlparse(base)
    return p1.scheme == p2.scheme and p1.netloc == p2.netloc


def extract_text(soup: BeautifulSoup) -> str:
    """Remove noise tags and extract body text via Trafilatura; fall back to BS4."""
    noise_tags = ["nav", "footer", "aside", "script", "style", "noscript"]
    for tag in soup.find_all(noise_tags):
        tag.decompose()
    text = trafilatura.extract(
        str(soup),
        include_comments=False,
        include_tables=True,
        no_fallback=False,
        target_language=None,
    )
    return (text or soup.get_text(separator="\n", strip=True)).strip()


def detect_lang(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < 100:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(
        1
        for c in text
        if ("぀" <= c <= "ヿ")  # Hiragana + Katakana
        or ("一" <= c <= "鿿")  # CJK Unified Ideographs
        or ("㐀" <= c <= "䶿")  # CJK Extension A
    )
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def parse_target_urls(target_raw: list[Any]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple) or len(entry) != 2:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls"
                f" (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result
