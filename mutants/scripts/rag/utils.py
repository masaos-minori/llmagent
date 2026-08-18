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


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_cosine_sim__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_cosine_sim__mutmut)
def cosine_sim(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_orig(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_1(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = None
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_2(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(None)
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_3(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x / y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_4(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(None, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_5(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, None))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_6(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_7(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, ))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_8(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = None
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_9(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(None)
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_10(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(None))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_11(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x / x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_12(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = None
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_13(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(None)
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_14(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(None))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_15(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y / y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_16(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 and mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_17(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a != 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_18(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 1.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_19(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b != 0.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_20(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 1.0:
        return 0.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_21(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 1.0
    return dot / (mag_a * mag_b)


def x_cosine_sim__mutmut_22(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot * (mag_a * mag_b)


def x_cosine_sim__mutmut_23(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors; returns 0.0 when either has zero magnitude."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0.0 or mag_b == 0.0:
        return 0.0
    return dot / (mag_a / mag_b)

mutants_x_cosine_sim__mutmut['_mutmut_orig'] = x_cosine_sim__mutmut_orig # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_1'] = x_cosine_sim__mutmut_1 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_2'] = x_cosine_sim__mutmut_2 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_3'] = x_cosine_sim__mutmut_3 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_4'] = x_cosine_sim__mutmut_4 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_5'] = x_cosine_sim__mutmut_5 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_6'] = x_cosine_sim__mutmut_6 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_7'] = x_cosine_sim__mutmut_7 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_8'] = x_cosine_sim__mutmut_8 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_9'] = x_cosine_sim__mutmut_9 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_10'] = x_cosine_sim__mutmut_10 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_11'] = x_cosine_sim__mutmut_11 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_12'] = x_cosine_sim__mutmut_12 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_13'] = x_cosine_sim__mutmut_13 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_14'] = x_cosine_sim__mutmut_14 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_15'] = x_cosine_sim__mutmut_15 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_16'] = x_cosine_sim__mutmut_16 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_17'] = x_cosine_sim__mutmut_17 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_18'] = x_cosine_sim__mutmut_18 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_19'] = x_cosine_sim__mutmut_19 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_20'] = x_cosine_sim__mutmut_20 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_21'] = x_cosine_sim__mutmut_21 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_22'] = x_cosine_sim__mutmut_22 # type: ignore # mutmut generated
mutants_x_cosine_sim__mutmut['x_cosine_sim__mutmut_23'] = x_cosine_sim__mutmut_23 # type: ignore # mutmut generated
mutants_x_sanitize_document__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_sanitize_document__mutmut)
def sanitize_document(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[REMOVED]", text)
    return text


def x_sanitize_document__mutmut_orig(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[REMOVED]", text)
    return text


def x_sanitize_document__mutmut_1(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = None
    return text


def x_sanitize_document__mutmut_2(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub(None, text)
    return text


def x_sanitize_document__mutmut_3(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[REMOVED]", None)
    return text


def x_sanitize_document__mutmut_4(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub(text)
    return text


def x_sanitize_document__mutmut_5(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[REMOVED]", )
    return text


def x_sanitize_document__mutmut_6(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("XX[REMOVED]XX", text)
    return text


def x_sanitize_document__mutmut_7(text: str) -> str:
    """Remove known prompt injection patterns; return sanitized text."""
    # Contract: returns 0.0 equivalent — no error on clean text.
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub("[removed]", text)
    return text

mutants_x_sanitize_document__mutmut['_mutmut_orig'] = x_sanitize_document__mutmut_orig # type: ignore # mutmut generated
mutants_x_sanitize_document__mutmut['x_sanitize_document__mutmut_1'] = x_sanitize_document__mutmut_1 # type: ignore # mutmut generated
mutants_x_sanitize_document__mutmut['x_sanitize_document__mutmut_2'] = x_sanitize_document__mutmut_2 # type: ignore # mutmut generated
mutants_x_sanitize_document__mutmut['x_sanitize_document__mutmut_3'] = x_sanitize_document__mutmut_3 # type: ignore # mutmut generated
mutants_x_sanitize_document__mutmut['x_sanitize_document__mutmut_4'] = x_sanitize_document__mutmut_4 # type: ignore # mutmut generated
mutants_x_sanitize_document__mutmut['x_sanitize_document__mutmut_5'] = x_sanitize_document__mutmut_5 # type: ignore # mutmut generated
mutants_x_sanitize_document__mutmut['x_sanitize_document__mutmut_6'] = x_sanitize_document__mutmut_6 # type: ignore # mutmut generated
mutants_x_sanitize_document__mutmut['x_sanitize_document__mutmut_7'] = x_sanitize_document__mutmut_7 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_sanitize_document_full__mutmut)
def sanitize_document_full(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_orig(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_1(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = None
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_2(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(None):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_3(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(None)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_4(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = None
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_5(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub(None, text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_6(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", None)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_7(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub(text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_8(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", )
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_9(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("XX[REMOVED]XX", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_10(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[removed]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_11(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=None, was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_12(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=None, patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_13(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), patterns_detected=None
    )


def x_sanitize_document_full__mutmut_14(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        was_sanitized=bool(detected), patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_15(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, patterns_detected=detected
    )


def x_sanitize_document_full__mutmut_16(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(detected), )


def x_sanitize_document_full__mutmut_17(text: str) -> SanitizeResult:
    """Remove injection patterns; return SanitizeResult with audit trail."""
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
            text = pattern.sub("[REMOVED]", text)
    return SanitizeResult(
        text=text, was_sanitized=bool(None), patterns_detected=detected
    )

mutants_x_sanitize_document_full__mutmut['_mutmut_orig'] = x_sanitize_document_full__mutmut_orig # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_1'] = x_sanitize_document_full__mutmut_1 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_2'] = x_sanitize_document_full__mutmut_2 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_3'] = x_sanitize_document_full__mutmut_3 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_4'] = x_sanitize_document_full__mutmut_4 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_5'] = x_sanitize_document_full__mutmut_5 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_6'] = x_sanitize_document_full__mutmut_6 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_7'] = x_sanitize_document_full__mutmut_7 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_8'] = x_sanitize_document_full__mutmut_8 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_9'] = x_sanitize_document_full__mutmut_9 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_10'] = x_sanitize_document_full__mutmut_10 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_11'] = x_sanitize_document_full__mutmut_11 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_12'] = x_sanitize_document_full__mutmut_12 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_13'] = x_sanitize_document_full__mutmut_13 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_14'] = x_sanitize_document_full__mutmut_14 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_15'] = x_sanitize_document_full__mutmut_15 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_16'] = x_sanitize_document_full__mutmut_16 # type: ignore # mutmut generated
mutants_x_sanitize_document_full__mutmut['x_sanitize_document_full__mutmut_17'] = x_sanitize_document_full__mutmut_17 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_normalize_unicode__mutmut)
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


def x_normalize_unicode__mutmut_orig(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize("NFKC", text)


def x_normalize_unicode__mutmut_1(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize("NFKC", text)


def x_normalize_unicode__mutmut_2(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(None)
    return unicodedata.normalize("NFKC", text)


def x_normalize_unicode__mutmut_3(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(None).__name__}")
    return unicodedata.normalize("NFKC", text)


def x_normalize_unicode__mutmut_4(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize(None, text)


def x_normalize_unicode__mutmut_5(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize("NFKC", None)


def x_normalize_unicode__mutmut_6(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize(text)


def x_normalize_unicode__mutmut_7(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize("NFKC", )


def x_normalize_unicode__mutmut_8(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize("XXNFKCXX", text)


def x_normalize_unicode__mutmut_9(text: str) -> str:
    """Normalize full-width alphanumerics and variant characters via NFKC.

    NFKC converts, for example, full-width digits/Latin letters to their
    ASCII equivalents and decomposes compatibility characters.  This keeps
    RAG index tokens consistent regardless of input encoding style.

    Raises TypeError if *text* is not a str.
    """
    if not isinstance(text, str):
        raise TypeError(f"normalize_unicode expects str, got {type(text).__name__}")
    return unicodedata.normalize("nfkc", text)

mutants_x_normalize_unicode__mutmut['_mutmut_orig'] = x_normalize_unicode__mutmut_orig # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_1'] = x_normalize_unicode__mutmut_1 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_2'] = x_normalize_unicode__mutmut_2 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_3'] = x_normalize_unicode__mutmut_3 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_4'] = x_normalize_unicode__mutmut_4 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_5'] = x_normalize_unicode__mutmut_5 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_6'] = x_normalize_unicode__mutmut_6 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_7'] = x_normalize_unicode__mutmut_7 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_8'] = x_normalize_unicode__mutmut_8 # type: ignore # mutmut generated
mutants_x_normalize_unicode__mutmut['x_normalize_unicode__mutmut_9'] = x_normalize_unicode__mutmut_9 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_floats_to_blob__mutmut)
def floats_to_blob(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), exc)
        raise


def x_floats_to_blob__mutmut_orig(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), exc)
        raise


def x_floats_to_blob__mutmut_1(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(None)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), exc)
        raise


def x_floats_to_blob__mutmut_2(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(None, *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), exc)
        raise


def x_floats_to_blob__mutmut_3(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(*values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), exc)
        raise


def x_floats_to_blob__mutmut_4(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", )
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), exc)
        raise


def x_floats_to_blob__mutmut_5(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error(None, len(values), exc)
        raise


def x_floats_to_blob__mutmut_6(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", None, exc)
        raise


def x_floats_to_blob__mutmut_7(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), None)
        raise


def x_floats_to_blob__mutmut_8(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error(len(values), exc)
        raise


def x_floats_to_blob__mutmut_9(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", exc)
        raise


def x_floats_to_blob__mutmut_10(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("Failed to pack %d floats into BLOB: %s", len(values), )
        raise


def x_floats_to_blob__mutmut_11(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("XXFailed to pack %d floats into BLOB: %sXX", len(values), exc)
        raise


def x_floats_to_blob__mutmut_12(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("failed to pack %d floats into blob: %s", len(values), exc)
        raise


def x_floats_to_blob__mutmut_13(values: list[float]) -> bytes:
    """Convert a list of floats to a little-endian float32 BLOB for sqlite-vec.

    The sqlite-vec MATCH operator requires embeddings stored as
    little-endian 32-bit floats packed contiguously in a BLOB.

    Raises TypeError  if *values* is not a list.
    Raises ValueError if *values* is empty, contains non-numeric elements,
                      or contains non-finite values (NaN, inf, -inf).
    Raises struct.error if packing fails (e.g. value out of float32 range).
    """
    _validate_float_list(values)
    try:
        return struct.pack(f"<{len(values)}f", *values)
    except struct.error as exc:
        logger.error("FAILED TO PACK %D FLOATS INTO BLOB: %S", len(values), exc)
        raise

mutants_x_floats_to_blob__mutmut['_mutmut_orig'] = x_floats_to_blob__mutmut_orig # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_1'] = x_floats_to_blob__mutmut_1 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_2'] = x_floats_to_blob__mutmut_2 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_3'] = x_floats_to_blob__mutmut_3 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_4'] = x_floats_to_blob__mutmut_4 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_5'] = x_floats_to_blob__mutmut_5 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_6'] = x_floats_to_blob__mutmut_6 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_7'] = x_floats_to_blob__mutmut_7 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_8'] = x_floats_to_blob__mutmut_8 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_9'] = x_floats_to_blob__mutmut_9 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_10'] = x_floats_to_blob__mutmut_10 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_11'] = x_floats_to_blob__mutmut_11 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_12'] = x_floats_to_blob__mutmut_12 # type: ignore # mutmut generated
mutants_x_floats_to_blob__mutmut['x_floats_to_blob__mutmut_13'] = x_floats_to_blob__mutmut_13 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate_url__mutmut)
def validate_url(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def x_validate_url__mutmut_orig(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def x_validate_url__mutmut_1(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = None
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def x_validate_url__mutmut_2(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(None)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def x_validate_url__mutmut_3(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") or bool(parsed.netloc)


def x_validate_url__mutmut_4(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme not in ("http", "https") and bool(parsed.netloc)


def x_validate_url__mutmut_5(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("XXhttpXX", "https") and bool(parsed.netloc)


def x_validate_url__mutmut_6(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("HTTP", "https") and bool(parsed.netloc)


def x_validate_url__mutmut_7(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "XXhttpsXX") and bool(parsed.netloc)


def x_validate_url__mutmut_8(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "HTTPS") and bool(parsed.netloc)


def x_validate_url__mutmut_9(url: str) -> bool:
    """Return True if the URL has a valid http/https scheme and a non-empty netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and bool(None)

mutants_x_validate_url__mutmut['_mutmut_orig'] = x_validate_url__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_1'] = x_validate_url__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_2'] = x_validate_url__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_3'] = x_validate_url__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_4'] = x_validate_url__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_5'] = x_validate_url__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_6'] = x_validate_url__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_7'] = x_validate_url__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_8'] = x_validate_url__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate_url__mutmut['x_validate_url__mutmut_9'] = x_validate_url__mutmut_9 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut: MutantDict = {}  # type: ignore


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


@_mutmut_mutated(mutants_x__validate_float_list__mutmut)
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


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_orig(values: list[float]) -> None:
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


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_1(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if isinstance(values, list):
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


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_2(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            None,
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


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_3(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            f"floats_to_blob expects list[float], got {type(None).__name__}",
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


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_4(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            f"floats_to_blob expects list[float], got {type(values).__name__}",
        )
    if values:
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


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_5(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            f"floats_to_blob expects list[float], got {type(values).__name__}",
        )
    if not values:
        raise ValueError(None)
    for i, v in enumerate(values):
        if not isinstance(v, int | float):
            raise ValueError(
                f"floats_to_blob: element {i} must be numeric, got {type(v).__name__}",
            )
        if not math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_6(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            f"floats_to_blob expects list[float], got {type(values).__name__}",
        )
    if not values:
        raise ValueError("XXfloats_to_blob received an empty list.XX")
    for i, v in enumerate(values):
        if not isinstance(v, int | float):
            raise ValueError(
                f"floats_to_blob: element {i} must be numeric, got {type(v).__name__}",
            )
        if not math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_7(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            f"floats_to_blob expects list[float], got {type(values).__name__}",
        )
    if not values:
        raise ValueError("FLOATS_TO_BLOB RECEIVED AN EMPTY LIST.")
    for i, v in enumerate(values):
        if not isinstance(v, int | float):
            raise ValueError(
                f"floats_to_blob: element {i} must be numeric, got {type(v).__name__}",
            )
        if not math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_8(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            f"floats_to_blob expects list[float], got {type(values).__name__}",
        )
    if not values:
        raise ValueError("floats_to_blob received an empty list.")
    for i, v in enumerate(None):
        if not isinstance(v, int | float):
            raise ValueError(
                f"floats_to_blob: element {i} must be numeric, got {type(v).__name__}",
            )
        if not math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_9(values: list[float]) -> None:
    """Guard: ensure *values* is a non-empty list of finite numeric elements."""
    if not isinstance(values, list):
        raise TypeError(
            f"floats_to_blob expects list[float], got {type(values).__name__}",
        )
    if not values:
        raise ValueError("floats_to_blob received an empty list.")
    for i, v in enumerate(values):
        if isinstance(v, int | float):
            raise ValueError(
                f"floats_to_blob: element {i} must be numeric, got {type(v).__name__}",
            )
        if not math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_10(values: list[float]) -> None:
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
                None,
            )
        if not math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_11(values: list[float]) -> None:
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
                f"floats_to_blob: element {i} must be numeric, got {type(None).__name__}",
            )
        if not math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_12(values: list[float]) -> None:
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
        if math.isfinite(v):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_13(values: list[float]) -> None:
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
        if not math.isfinite(None):
            raise ValueError(
                f"floats_to_blob: element {i} is not finite ({v!r})",
            )


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def x__validate_float_list__mutmut_14(values: list[float]) -> None:
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
                None,
            )

mutants_x__validate_float_list__mutmut['_mutmut_orig'] = x__validate_float_list__mutmut_orig # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_1'] = x__validate_float_list__mutmut_1 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_2'] = x__validate_float_list__mutmut_2 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_3'] = x__validate_float_list__mutmut_3 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_4'] = x__validate_float_list__mutmut_4 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_5'] = x__validate_float_list__mutmut_5 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_6'] = x__validate_float_list__mutmut_6 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_7'] = x__validate_float_list__mutmut_7 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_8'] = x__validate_float_list__mutmut_8 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_9'] = x__validate_float_list__mutmut_9 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_10'] = x__validate_float_list__mutmut_10 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_11'] = x__validate_float_list__mutmut_11 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_12'] = x__validate_float_list__mutmut_12 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_13'] = x__validate_float_list__mutmut_13 # type: ignore # mutmut generated
mutants_x__validate_float_list__mutmut['x__validate_float_list__mutmut_14'] = x__validate_float_list__mutmut_14 # type: ignore # mutmut generated
