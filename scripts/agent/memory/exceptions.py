"""agent/memory/exceptions.py

Domain exceptions for the persistent memory layer.
"""

from __future__ import annotations


class MemorySchemaError(ValueError):
    """Raised when a memory row or field fails schema validation."""


class UnknownMemoryTypeError(MemorySchemaError):
    """Raised when an unrecognized memory_type value is encountered."""

    def __init__(self, memory_type: str) -> None:
        super().__init__(f"Unknown memory type: {memory_type!r}")


class MemoryStorageError(RuntimeError):
    """Raised when a DB write operation fails."""


class JsonlFormatError(ValueError):
    """Raised when a JSONL line cannot be parsed or fails schema validation."""


class MemoryConsistencyError(RuntimeError):
    """Raised when memories / memories_fts / memories_vec counts are inconsistent."""


class EmbeddingTransportError(RuntimeError):
    """Raised when an HTTP-level error prevents embedding retrieval."""


class EmbeddingProtocolError(ValueError):
    """Raised when the embedding service response violates the expected schema."""


class ExtractionError(RuntimeError):
    """Raised when memory extraction from conversation history fails."""


class InjectionValidationError(ValueError):
    """Raised when injection inputs fail validation (e.g. empty query)."""
