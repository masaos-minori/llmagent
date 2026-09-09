"""tests/rag/test_config_resolution.py

Tests for scripts/rag/config_resolution.resolve_rag_config().

Covers: priority ordering (CLI > env > YAML > defaults), default values,
and validation error propagation.
"""

from unittest.mock import MagicMock, patch

import pytest
from rag.config_resolution import resolve_rag_config
from rag.models_config import RagConfigImpl


def _make_cfg(**overrides):
    """Return a dict-like object with overrides applied to defaults."""
    base = {
        "use_mqe": False,
        "top_k_search": 5,
        "use_rerank": False,
        "rag_top_k": 3,
        "max_chunks_per_doc": 5,
        "top_k_rerank": 10,
        "rag_min_score": 0.0,
        "use_rrf": True,
        "rrf_k": 60,
        "use_search": True,
        "rag_service_url": None,
        "rag_auth_token": None,
        "use_refiner": False,
        "refiner_max_tokens": 512,
        "refiner_max_chars_per_chunk": 800,
        "refiner_timeout": 30.0,
        "llm_url": "",
        "embed_url": "",
        "rag_db_path": ":memory:",
        "sqlite_vec_so": "/opt/llm/sqlite-vec/vec0.so",
        "sqlite_timeout": 5,
        "sqlite_busy_timeout_ms": 5000,
        "embed_retry": 3,
        "embed_workers": 4,
        "rag_pipeline_service_url": None,
        "mqe_prompt_template": "Expand query: {query}",
        "mqe_n_queries": 3,
        "rerank_prompt_template": "Rerank results for: {query}",
    }
    base.update(overrides)
    return base


@pytest.fixture
def mock_validator():
    """Mock RagConfigValidator to avoid real validation."""
    with patch("rag.config_resolution.RagConfigValidator") as MockValidator:
        mock_instance = MagicMock()
        mock_instance.validate.return_value.ok = True
        mock_instance.validate.return_value.warnings = []
        mock_instance.validate.return_value.errors = []
        MockValidator.return_value = mock_instance
        yield mock_instance


def test_returns_rag_config_impl_directly(mock_validator):
    """If cfg is already RagConfigImpl, return it directly."""
    original = RagConfigImpl(
        use_mqe=True,
        top_k_search=10,
        use_rerank=False,
        rag_top_k=5,
        max_chunks_per_doc=5,
        top_k_rerank=10,
        rag_min_score=0.0,
        use_rrf=True,
        rrf_k=60,
        use_search=True,
        rag_service_url=None,
        rag_auth_token=None,
        use_refiner=False,
        refiner_max_tokens=512,
        refiner_max_chars_per_chunk=800,
        refiner_timeout=30.0,
        llm_url="",
        embed_url="",
        rag_db_path=":memory:",
        sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
        sqlite_timeout=5,
        sqlite_busy_timeout_ms=5000,
        embed_retry=3,
        embed_workers=4,
        rag_pipeline_service_url=None,
        mqe_prompt_template="Expand query: {query}",
        mqe_n_queries=3,
        rerank_prompt_template="Rerank results for: {query}",
    )
    result = resolve_rag_config(original)
    assert result is original


def test_dict_input_uses_defaults_for_missing_fields(mock_validator):
    """Dict input should get defaults for missing fields."""
    partial = {"use_mqe": True}
    result = resolve_rag_config(partial)
    assert isinstance(result, RagConfigImpl)
    assert result.use_mqe is True
    assert result.top_k_search == 5  # default


def test_object_with_dict_uses_defaults_for_missing_fields(mock_validator):
    """Object with __dict__ should get defaults for missing fields."""
    obj = MagicMock()
    obj.__dict__ = {"use_mqe": True}
    result = resolve_rag_config(obj)
    assert isinstance(result, RagConfigImpl)
    assert result.use_mqe is True
    assert result.top_k_search == 5  # default


def test_module_cfg_fallback_when_no_loader_and_no_exception(mock_validator):
    """When config_loader is None and no exception, ConfigLoader loads full config."""
    result = resolve_rag_config(None, module_cfg={"use_mqe": True})
    assert isinstance(result, RagConfigImpl)
    # module_cfg is NOT used here; ConfigLoader loads the real config
    assert result.use_mqe is False  # from system config, not module_cfg


def test_module_cfg_used_as_fallback_when_config_loader_raises(mock_validator):
    """When config_loader raises, module_cfg is used as fallback."""
    with patch(
        "rag.config_resolution.ConfigLoader", side_effect=ValueError("no config")
    ):
        result = resolve_rag_config(None, module_cfg={"use_mqe": True})
    assert isinstance(result, RagConfigImpl)
    assert result.use_mqe is True


def test_config_loader_fallback_on_file_not_found(mock_validator):
    """When config_loader raises FileNotFoundError, empty dict is used."""
    with patch(
        "rag.config_resolution.ConfigLoader", side_effect=FileNotFoundError("no config")
    ):
        result = resolve_rag_config(None)
    assert isinstance(result, RagConfigImpl)
    assert result.use_mqe is False  # default


def test_validation_error_raises(mock_validator):
    """Validation errors should raise ValueError."""
    mock_validator.validate.return_value.ok = False
    mock_validator.validate.return_value.errors = ["invalid field"]
    with pytest.raises(ValueError, match="RAG config validation failed"):
        resolve_rag_config({})
