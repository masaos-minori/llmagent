"""tests/test_config_validator.py — Startup validator for RAG config cross-file consistency."""
import pytest

from shared.config_validator import RagConfigValidator


class TestRagConfigValidator:
    def setup_method(self) -> None:
        self.validator = RagConfigValidator()

    def test_ok_no_errors(self) -> None:
        result = self.validator.validate({"rag": {}})
        assert result.ok is True
        assert len(result.errors) == 0

    def test_embedding_dim_mismatch(self) -> None:
        result = self.validator.validate({
            "rag": {"embedding_dim": 768, "vec_dim": 1536},
        })
        assert result.ok is False
        assert len(result.errors) == 1
        assert "embedding_dim=768 != vec_dim=1536" in result.errors[0]

    def test_embedding_dim_match(self) -> None:
        result = self.validator.validate({
            "rag": {"embedding_dim": 768, "vec_dim": 768},
        })
        assert result.ok is True

    def test_use_rrf_false_warning(self) -> None:
        result = self.validator.validate({
            "rag": {"use_rrf": False},
        })
        assert len(result.warnings) == 1
        assert "use_rrf=false" in result.warnings[0]

    def test_use_rrf_true_no_warning(self) -> None:
        result = self.validator.validate({
            "rag": {"use_rrf": True},
        })
        assert len(result.warnings) == 0

    def test_semantic_cache_threshold_low_warning(self) -> None:
        result = self.validator.validate({
            "rag": {"semantic_cache_threshold": 0.3},
        })
        assert len(result.warnings) == 1
        assert "semantic_cache_threshold=0.3" in result.warnings[0]

    def test_semantic_cache_threshold_normal_no_warning(self) -> None:
        result = self.validator.validate({
            "rag": {"semantic_cache_threshold": 0.92},
        })
        assert len(result.warnings) == 0

    def test_multiple_errors(self) -> None:
        result = self.validator.validate({
            "rag": {
                "embedding_dim": 768,
                "vec_dim": 1536,
                "use_rrf": False,
                "semantic_cache_threshold": 0.2,
            },
        })
        assert result.ok is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 2

    def test_no_rag_key(self) -> None:
        result = self.validator.validate({})
        assert result.ok is True
