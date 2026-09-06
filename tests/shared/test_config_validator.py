"""tests/test_config_validator.py — Startup validator for RAG config cross-file consistency."""

from shared.config_validator import RagConfigValidator


class TestRagConfigValidator:
    def setup_method(self) -> None:
        self.validator = RagConfigValidator()

    def test_ok_no_errors(self) -> None:
        result = self.validator.validate({"rag": {}})
        assert result.ok is True
        assert len(result.errors) == 0

    def test_use_rrf_false_warning(self) -> None:
        result = self.validator.validate(
            {
                "rag": {"use_rrf": False},
            }
        )
        assert len(result.warnings) == 1
        assert "use_rrf=false" in result.warnings[0]

    def test_use_rrf_true_no_warning(self) -> None:
        result = self.validator.validate(
            {
                "rag": {"use_rrf": True},
            }
        )
        assert len(result.warnings) == 0

    def test_multiple_errors(self) -> None:
        result = self.validator.validate(
            {
                "rag": {
                    "use_rrf": False,
                    "semantic_cache_threshold": 0.2,
                },
            }
        )
        assert result.ok is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert "semantic_cache_threshold" in result.errors[0]
        assert "use_rrf" in result.warnings[0]

    def test_no_rag_key(self) -> None:
        result = self.validator.validate({})
        assert result.ok is True

    def test_flat_shape_uses_root_dict(self) -> None:
        result = self.validator.validate(
            {
                "use_rrf": False,
                "semantic_cache_threshold": 0.2,
            }
        )
        assert result.ok is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert "semantic_cache_threshold" in result.errors[0]
        assert "use_rrf" in result.warnings[0]

    def test_flat_config_semantic_cache_max_size_present_error(self) -> None:
        result = self.validator.validate(
            {
                "semantic_cache_max_size": 100,
            }
        )
        assert result.ok is False
        assert len(result.errors) == 1
        assert "semantic_cache_max_size" in result.errors[0]

    def test_flat_config_use_rrf_false_warning(self) -> None:
        result = self.validator.validate(
            {
                "use_rrf": False,
            }
        )
        assert len(result.warnings) == 1
        assert "use_rrf=false" in result.warnings[0]

    def test_nested_config_semantic_cache_max_size_present_error(self) -> None:
        result = self.validator.validate(
            {
                "rag": {"semantic_cache_max_size": 100},
            }
        )
        assert result.ok is False
        assert len(result.errors) == 1
        assert "semantic_cache_max_size" in result.errors[0]

    def test_use_semantic_cache_present_error(self) -> None:
        result = self.validator.validate(
            {
                "rag": {"use_semantic_cache": True},
            }
        )
        assert result.ok is False
        assert "use_semantic_cache" in result.errors[0]

    def test_semantic_cache_threshold_present_error(self) -> None:
        result = self.validator.validate(
            {
                "rag": {"semantic_cache_threshold": 0.92},
            }
        )
        assert result.ok is False
        assert "semantic_cache_threshold" in result.errors[0]

    def test_all_three_removed_keys_produce_one_combined_error(self) -> None:
        result = self.validator.validate(
            {
                "rag": {
                    "use_semantic_cache": True,
                    "semantic_cache_threshold": 0.92,
                    "semantic_cache_max_size": 100,
                },
            }
        )
        assert result.ok is False
        assert len(result.errors) == 1
        assert "use_semantic_cache" in result.errors[0]
        assert "semantic_cache_threshold" in result.errors[0]
        assert "semantic_cache_max_size" in result.errors[0]
