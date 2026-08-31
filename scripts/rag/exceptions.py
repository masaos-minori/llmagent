"""scripts/rag/exceptions.py

Exception hierarchy for the RAG and ingestion layer.
"""

from __future__ import annotations

from enum import StrEnum


class RagLayerError(Exception):
    """Base for all rag/ exceptions."""


class EmbeddingSchemaError(RagLayerError, ValueError):
    """Raised when an embedding service response does not match expected schema."""


class PipelineValidationError(RagLayerError, RuntimeError):
    """Raised when a pipeline stage receives invalid configuration or input."""


class SearchQueryError(RagLayerError, ValueError):
    """Raised when a search query cannot be executed."""


class ChunkFormatError(RagLayerError, ValueError):
    """Raised when a chunk document does not match expected structure."""


class TokenizationError(RagLayerError, RuntimeError):
    """Raised when a tokenization step fails."""


class UnknownMetadataError(RagLayerError, ValueError):
    """Raised when metadata field has an unexpected value."""


class IngestionFailureReason(StrEnum):
    """Reason why a chunk ingestion failed."""

    PARSE_FAILED = "parse_failed"
    VALIDATION_FAILED = "validation_failed"
    EMBEDDING_FAILED = "embedding_failed"
    STORAGE_FAILED = "storage_failed"
    UNEXPECTED_FAILURE = "unexpected_failure"
    GROUP_VALIDATION_FAILED = "group_validation_failed"
