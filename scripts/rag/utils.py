#!/usr/bin/env python3
"""scripts/rag/utils.py

Shared utilities for the RAG ingestion pipeline
(Crawler, ChunkSplitter, RagIngester, agent_rag).
"""

import logging
import math
import re
import struct
import unicodedata
from urllib.parse import urlparse

from rag.models_result import SanitizeResult

MIN_TEXT_LENGTH_FOR_DETECTION = 100

# Structured log field keys for RAG lifecycle tracing
LOG_KEY_URL = "url"
LOG_KEY_DOC_ID = "doc_id"
LOG_KEY_CHUNK_ID = "chunk_id"
LOG_KEY_SOURCE_TYPE = "source_type"
LOG_KEY_STAGE_NAME = "stage_name"

# Float32 maximum magnitude; elements beyond this cannot be packed by
# floats_to_blob and are rejected with a typed ValueError before struct.pack.
_FLOAT32_MAX = 3.4028234663852886e38

# Library module — no FileHandler; caller controls log routing
logger = logging.getLogger(__name__)

# Patterns known to be used in prompt injection attacks
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(ignore\s+(?:(?:all|previous)\s+)*instructions?)", re.MULTILINE),
    re.compile(r"(?i)(system\s*:\s*)", re.MULTILINE),
    re.compile(r"(?i)\[SYSTEM\s*OVERRIDE\]", re.MULTILINE),
    re.compile(
        r"(?i)(disregard\s+(?:(?:all|prior|previous)\s+)*instructions?)", re.MULTILINE
    ),
    re.compile(r"(?i)(new\s+instructions?:)", re.MULTILINE),
]

# Boundary markers for the RAG context block. Defined once in the lowest layer
# of the rag package so every formatting site imports the same strings.
RAG_BLOCK_START = "[RAG_CONTEXT_START]"
RAG_BLOCK_END = "[RAG_CONTEXT_END]"

# Neutralizes the boundary markers inside untrusted text so crawled content
# cannot close or reopen the block. Case-insensitive, tolerant of whitespace
# inside the brackets; the alternation is derived from the two constants so a
# single definition drives both.
_MARKER_PATTERN = re.compile(
    r"(?i)\[\s*"
    + re.escape(RAG_BLOCK_START[1:-1])
    + r"\s*\]|\[\s*"
    + re.escape(RAG_BLOCK_END[1:-1])
    + r"\s*\]",
    re.MULTILINE,
)


def cosine_sim(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def sanitize_document(text: str) -> str:
    """Remove known prompt injection patterns and boundary markers; return sanitized text."""
    # Contract: returns clean text unchanged — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[REMOVED]", text)
    # Neutralize any boundary marker left in untrusted content so it cannot
    # close or reopen the RAG context block. Runs after phrase substitution.
    text = _MARKER_PATTERN.sub("[REMOVED]", text)
    return text


def sanitize_field(value: str) -> str:
    """Sanitize a single-line field (a chunk title or url).

    Collapses control characters and Unicode line/paragraph separators to
    single spaces, then applies :func:`sanitize_document`, then strips. Used
    for header fields so a title cannot start a new line that mimics a header
    or a boundary marker. Content keeps its line structure and never uses this.
    """
    collapsed = re.sub(r"[\s\u0000-\u001f\u007f\u2028\u2029]+", " ", value)
    return sanitize_document(collapsed).strip()


def sanitize_document_full(text: str) -> SanitizeResult:
    """Remove injection patterns and boundary markers; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    if _MARKER_PATTERN.search(text):
        detected.append(_MARKER_PATTERN.pattern)
        text = _MARKER_PATTERN.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def normalize_unicode(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize("NFKC", text)


def floats_to_blob(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      contains non-finite values (NaN, inf, -inf), or contains
                      values outside the float32 range (abs > _FLOAT32_MAX).
    Raises struct.error if a residual packing failure occurs after validation.
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), exc)
        raise


def validate_url(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _validate_float_list(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            f"floats_to_blob expects list[float], got {type(values).__name__}",
        )
    if not values:
        raise ValueError("floats_to_blob received an empty list.")
    for i, v in enumerate(values):
        if not isinstance(v, int | float):
            raise ValueError(
                f"floats_to_blob: element {i} must be numeric, got {type(v).__name__}",
            )
        if not math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )
        if abs(v) > _FLOAT32_MAX:
            raise ValueError(
                f"floats_to_blob: element {i} is out of float32 range ({v!r})",
            )
