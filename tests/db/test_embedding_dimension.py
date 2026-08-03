"""tests/test_embedding_dimension.py
Unit tests for embedding dimension constant:
- get_embedding_dims() returns the fixed QWEN3_EMBEDDING_DIMS value (1024)
"""

from __future__ import annotations

from db.store_protocols import get_embedding_dims


def test_get_embedding_dims_returns_constant() -> None:
    """get_embedding_dims() always returns 1024 regardless of config."""
    assert get_embedding_dims() == 1024
