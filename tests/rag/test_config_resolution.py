"""tests/rag/test_config_resolution.py

Tests for scripts/rag/config_resolution.resolve_rag_config().

Covers: priority ordering (CLI > env > YAML > defaults), default values,
non-mutation, required rag_db_path when use_search, module_cfg layering,
and validation error propagation.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from rag.config_resolution import resolve_rag_config
from rag.models_config import RagConfigImpl
from rag.pipeline import RagPipeline


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
        "rag_query_service_url": None,
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
        rag_query_service_url=None,
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


def test_non_string_template_raises():
    """A non-string prompt template fails fast via the real validator."""
    with pytest.raises(ValueError, match="RAG config validation failed"):
        resolve_rag_config(
            {
                "use_search": False,
                "mqe_prompt_template": 123,
                "rerank_prompt_template": "Rerank results for: {query}",
            }
        )


def test_valid_string_templates_resolve():
    """Valid string templates resolve normally through the real validator."""
    result = resolve_rag_config(
        {
            "use_search": False,
            "mqe_prompt_template": "Expand query: {query}",
            "rerank_prompt_template": "Rerank results for: {query}",
        }
    )
    assert isinstance(result, RagConfigImpl)
    assert result.mqe_prompt_template == "Expand query: {query}"
    assert result.rerank_prompt_template == "Rerank results for: {query}"


def test_renamed_key_resolves_and_old_spelling_ignored(mock_validator):
    """rag003 AC-2: the renamed key resolves; the old spelling is filtered out.

    `rag_query_service_url` is the query-path key. A config dict carrying the
    pre-rename spelling `rag_service_url` is an extra key for the _ALL_FIELDS
    filter and must stay None (fail-safe: no HTTP delegation).
    """
    result = resolve_rag_config({"rag_query_service_url": "http://x"})
    assert result.rag_query_service_url == "http://x"

    result = resolve_rag_config({"rag_service_url": "http://x"})
    assert result.rag_query_service_url is None


def _adapter_cfg(**overrides) -> SimpleNamespace:
    """Adapter-shaped RagConfig lacking rag_db_path (as build_rag_cfg_adapter produces)."""
    attrs = dict(
        use_search=True,
        rag_query_service_url="",
        use_refiner=False,
        use_mqe=False,
        use_rerank=False,
        use_rrf=True,
        rrf_k=60,
        top_k_search=5,
        rag_top_k=3,
        top_k_rerank=10,
        rag_min_score=0.0,
        max_chunks_per_doc=3,
        refiner_max_tokens=256,
        refiner_max_chars_per_chunk=500,
        refiner_timeout=10.0,
        llm_url="http://localhost:8000/v1/chat/completions",
        embed_url="http://localhost:8000/v1/embeddings",
        sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
        embed_retry=3,
        embed_workers=4,
        rag_pipeline_service_url=None,
        mqe_prompt_template="Expand query: {query}",
        rerank_prompt_template="Rerank results for: {query}",
        rag_auth_token="",
    )
    attrs.update(overrides)
    return SimpleNamespace(**attrs)


def test_dict_input_is_not_mutated(mock_validator):
    """REQ-001/AC-1: resolving a dict adds no keys and changes no values."""
    original = {"use_search": False, "top_k_search": 42}
    snapshot = dict(original)
    result = resolve_rag_config(original)
    assert original == snapshot
    assert isinstance(result, RagConfigImpl)
    assert result.top_k_search == 42


def test_object_input_is_not_mutated(mock_validator):
    """REQ-001/AC-1: resolving an object adds no attributes and changes no values."""
    original = SimpleNamespace(use_search=False, top_k_search=42)
    before = dict(vars(original))
    result = resolve_rag_config(original)
    after = dict(vars(original))
    assert before == after
    assert isinstance(result, RagConfigImpl)
    assert result.top_k_search == 42


def test_missing_rag_db_path_raises_when_use_search(mock_validator):
    """REQ-002/AC-2: a missing rag_db_path with use_search=True raises naming it."""
    with pytest.raises(ValueError, match="rag_db_path"):
        resolve_rag_config(
            {"use_search": True, "llm_url": "http://l", "embed_url": "http://e"}
        )


def test_empty_rag_db_path_raises_when_use_search(mock_validator):
    """REQ-002/AC-2: an empty rag_db_path with use_search=True raises naming it."""
    with pytest.raises(ValueError, match="rag_db_path"):
        resolve_rag_config(
            {
                "use_search": True,
                "rag_db_path": "",
                "llm_url": "http://l",
                "embed_url": "http://e",
            }
        )


def test_none_rag_db_path_raises_when_use_search(mock_validator):
    """REQ-002/AC-2: a None rag_db_path with use_search=True raises naming it."""
    with pytest.raises(ValueError, match="rag_db_path"):
        resolve_rag_config(
            {
                "use_search": True,
                "rag_db_path": None,
                "llm_url": "http://l",
                "embed_url": "http://e",
            }
        )


def test_all_empty_required_fields_named_together(mock_validator):
    """REQ-002/AC-2: all empty required fields are named together in one message."""
    with pytest.raises(ValueError) as excinfo:
        resolve_rag_config({"use_search": True})
    message = str(excinfo.value)
    assert "rag_db_path" in message
    assert "llm_url" in message
    assert "embed_url" in message


def test_use_search_false_without_path_resolves(mock_validator):
    """REQ-002/AC-2: use_search=False without a path still resolves."""
    result = resolve_rag_config({"use_search": False})
    assert isinstance(result, RagConfigImpl)


def test_module_cfg_layers_below_cfg_and_fills_missing(mock_validator):
    """REQ-003/AC-3: module_cfg fills missing keys; a cfg key beats the same module_cfg key."""
    adapter = _adapter_cfg(top_k_search=55)
    module_cfg = {
        "rag_db_path": "/x",
        "sqlite_timeout": 9,
        "mqe_n_queries": 7,
        "top_k_search": 111,
    }
    result = resolve_rag_config(adapter, module_cfg=module_cfg)
    assert result.rag_db_path == "/x"
    assert result.sqlite_timeout == 9
    assert result.mqe_n_queries == 7
    assert result.top_k_search == 55


def test_service_shape_resolves_module_cfg_db_path():
    """REQ-005/AC-5: a service-shaped RagPipeline gets its db path from module_cfg."""
    adapter = _adapter_cfg()
    module_cfg = {"rag_db_path": "/x", "sqlite_timeout": 9, "mqe_n_queries": 7}
    pipeline = RagPipeline(MagicMock(), adapter, module_cfg=module_cfg)
    assert pipeline._rag_db_path == "/x"
