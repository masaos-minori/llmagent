"""rag/exceptions.py
Exception hierarchy for the RAG and ingestion layer.
"""

from __future__ import annotations


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
