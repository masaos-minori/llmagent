from __future__ import annotations

from shared.production_config_validator import ProductionConfigValidator


class TestProductionConfigValidator:
    def test_plugin_strict_false_returns_error(self) -> None:
        config = {"plugin_strict": False, "tool_definitions_strict": True, "routing_drift_strict": True, "use_tool_dag": True}
        result = ProductionConfigValidator().validate(config)
        assert len(result.errors) == 1
        assert "plugin_strict" in result.errors[0]

    def test_all_true_returns_no_errors(self) -> None:
        config = {"plugin_strict": True, "tool_definitions_strict": True, "routing_drift_strict": True, "use_tool_dag": True}
        result = ProductionConfigValidator().validate(config)
        assert result.errors == []

    def test_all_absent_returns_four_errors(self) -> None:
        config: dict[str, bool] = {}
        result = ProductionConfigValidator().validate(config)
        assert len(result.errors) == 4

    def test_use_tool_dag_false_returns_error(self) -> None:
        config = {"plugin_strict": True, "tool_definitions_strict": True, "routing_drift_strict": True, "use_tool_dag": False}
        result = ProductionConfigValidator().validate(config)
        assert len(result.errors) == 1
        assert "use_tool_dag" in result.errors[0]

    def test_validate_unknown_tool_safety_tiers_empty(self) -> None:
        result = ProductionConfigValidator().validate_unknown_tool_safety_tiers([])
        assert result.errors == []

    def test_validate_unknown_tool_safety_tiers_with_mdq(self) -> None:
        result = ProductionConfigValidator().validate_unknown_tool_safety_tiers(["mdq"])
        assert len(result.errors) == 1
        assert "mdq" in result.errors[0]
