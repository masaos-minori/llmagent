#!/usr/bin/env python3
"""scripts/rag/ingestion/crawler_utils.py

Pure-function utilities for WebCrawler: URL helpers, content extraction,
language detection, target URL parsing, and the redirect trust-boundary policy
helpers (REQ-002).

Extracted from web_crawler.py to keep WebCrawler under 400 lines.
"""

from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
import socket
import tomllib
from pathlib import Path
from urllib.parse import urldefrag, urlparse

import trafilatura
from bs4 import BeautifulSoup
from rag.utils import MIN_TEXT_LENGTH_FOR_DETECTION, validate_url

logger = logging.getLogger(__name__)

# Supported language codes for resolved (output) lang values
_SUPPORTED_LANGS: frozenset[str] = frozenset({"en", "ja"})
# Valid hint lang values including "auto" for per-page CJK-ratio detection
_VALID_HINT_LANGS: frozenset[str] = frozenset({"en", "ja", "auto"})
# CJK character ratio threshold above which text is classified as Japanese
_CJK_RATIO_THRESHOLD: float = 0.1

# Expected element count for target_urls entries: [url, lang]
_TARGET_URL_ENTRY_LENGTH = 2


def _validate_target_url(url: str) -> bool:
    """Return True when url has an accepted scheme (http, https, or file).

    Unlike validate_url() in rag.utils, this function also accepts file://
    URIs used by the --targets-file crawl path.
    """
    from urllib.parse import urlparse

    scheme = urlparse(url).scheme
    return scheme in {"http", "https", "file"}


def parse_targets_file(path: Path) -> list[tuple[str, str]]:
    """Read a TOML targets file and return validated (url, lang) pairs.

    The file must contain a ``target_urls`` key with a list of [url, lang]
    2-element lists, matching the format used in config/rag_pipeline.toml.

    Raises:
        FileNotFoundError: when the file does not exist.
        ValueError: when an entry has an unsupported URL scheme or an invalid
            lang value.
    """
    raw_text = path.read_text(encoding="utf-8")
    data = tomllib.loads(raw_text)
    target_raw: list[list[str]] = data.get("target_urls", [])
    result: list[tuple[str, str]] = []
    for i, entry in enumerate(target_raw):
        if (
            not isinstance(entry, list | tuple)
            or len(entry) != _TARGET_URL_ENTRY_LENGTH
        ):
            raise ValueError(
                f"targets-file entry [{i}] must be a 2-element list [url, lang]"
            )
        url, lang = str(entry[0]), str(entry[1])
        if not _validate_target_url(url):
            raise ValueError(
                f"targets-file entry [{i}]: unsupported URL scheme in {url!r} (must be http, https, or file)"
            )
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"targets-file entry [{i}]: unsupported lang {lang!r} (must be one of {sorted(_VALID_HINT_LANGS)})"
            )
        result.append((url, lang))
    return result


# Unicode code point ranges for CJK character detection in detect_lang()
_HIRAGANA_KATAKANA_START = "぀"
_HIRAGANA_KATAKANA_END = "ヿ"
_CJK_UNIFIED_START = "一"
_CJK_UNIFIED_END = "鿿"
_CJK_EXT_A_START = "㐀"
_CJK_EXT_A_END = "䶿"


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


def redirect_allowed(origin: str, target: str) -> bool:
    """Return True when a redirect hop may be followed from the crawl origin.

    Compares the hop ``target`` against the crawl ``origin`` by hostname, so a
    same-host redirect is allowed; a single http-to-https scheme upgrade is
    permitted while a downgrade (https to http) is refused. Default ports are
    normalized away via ``urlparse.hostname``, so ``http://example.com`` and
    ``https://example.com`` compare equal. A different host is refused here and
    falls through to the non-public-address check in ``host_is_public``.
    """
    p_origin = urlparse(origin)
    p_target = urlparse(target)
    if p_origin.hostname != p_target.hostname:
        return False
    o_scheme, t_scheme = p_origin.scheme, p_target.scheme
    if o_scheme != t_scheme:
        return o_scheme == "http" and t_scheme == "https"
    return True


def _ip_is_public(ip: str) -> bool:
    """Return True when a single resolved address is a global (public) address.

    Fails closed: an unparseable address is treated as non-public. An address is
    public only when it is not private, loopback, link-local, reserved,
    multicast, or unspecified.
    """
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return (
        not address.is_private
        and not address.is_loopback
        and not address.is_link_local
        and not address.is_reserved
        and not address.is_multicast
        and not address.is_unspecified
    )


async def host_is_public(host: str) -> bool:
    """Return True when every address ``host`` resolves to is public.

    Resolves once with the running event loop's asynchronous resolver (so it
    never blocks the loop on a synchronous getaddrinfo) and applies
    :func:`_ip_is_public` to each result. A resolution failure or an empty
    result fails closed and returns False. Name resolution here is before the
    request and is not pinned to the connection, so a DNS-rebinding attacker is
    not fully excluded.
    """
    try:
        addr_infos = await asyncio.get_event_loop().getaddrinfo(host, None)
    except (socket.gaierror, OSError, RuntimeError) as e:
        logger.debug("resolve %s failed: %s", host, e)
        return False
    # No addresses returned: the host could not be established as public, so
    # fail closed rather than treating an empty result as vacuously public.
    if not addr_infos:
        return False
    for info in addr_infos:
        ip = info[4][0]
        if "%" in ip:
            ip = ip.split("%", 1)[0]
        if not _ip_is_public(ip):
            return False
    return True


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
    fallback = soup.get_text(separator="\n", strip=True)
    extracted: str = text or fallback
    return extracted.strip()


def detect_lang(text: str) -> str | None:
    """Detect language by CJK character ratio.

    Returns 'ja' when CJK ratio >= _CJK_RATIO_THRESHOLD, 'en' otherwise.
    Returns None for texts shorter than 100 characters (too short for reliable
    detection).
    """
    if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
        return None
    # Count Hiragana, Katakana, and CJK Unified Ideographs (incl. Extension A)
    cjk_count = sum(1 for c in text if _is_cjk_char(c))
    return "ja" if cjk_count / len(text) >= _CJK_RATIO_THRESHOLD else "en"


def _is_cjk_char(c: str) -> bool:
    """Check if a character is CJK (Hiragana, Katakana, or CJK Unified Ideograph)."""
    return (
        (_HIRAGANA_KATAKANA_START <= c <= _HIRAGANA_KATAKANA_END)
        or (_CJK_UNIFIED_START <= c <= _CJK_UNIFIED_END)
        or (_CJK_EXT_A_START <= c <= _CJK_EXT_A_END)
    )


def parse_target_urls(target_raw: list[list[str]]) -> list[tuple[str, str]]:
    """Validate and parse the target_urls config list into (url, lang) tuples."""
    result: list[tuple[str, str]] = []
    for entry in target_raw:
        if not isinstance(entry, list | tuple):
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        if len(entry) != _TARGET_URL_ENTRY_LENGTH:
            raise ValueError(
                "Each entry in target_urls must be a 2-element list of [url, lang]",
            )
        url_raw, lang_raw = str(entry[0]), str(entry[1])
        if not isinstance(url_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        if not isinstance(lang_raw, str):
            raise ValueError(
                f"target_urls entry must be [str, str], got [{type(url_raw).__name__}, {type(lang_raw).__name__}]"
            )
        url, lang = url_raw, lang_raw
        if not validate_url(url):
            raise ValueError(f"Invalid URL in target_urls: {url!r}")
        if lang not in _VALID_HINT_LANGS:
            raise ValueError(
                f"Unsupported lang {lang!r} in target_urls (must be one of {sorted(_VALID_HINT_LANGS)})",
            )
        result.append((url, lang))
    return result
