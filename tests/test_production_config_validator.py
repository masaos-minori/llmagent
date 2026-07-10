from __future__ import annotations

import pytest
from shared.mcp_config import SecurityProfile
from shared.production_config_validator import ProductionConfigValidator


class TestProductionConfigValidatorStrictKeys:
    """Tests for strict key validation (plugin_strict, tool_definitions_strict, routing_drift_strict)."""

    @pytest.mark.parametrize(
        "strict_key",
        ["plugin_strict", "tool_definitions_strict", "routing_drift_strict"],
    )
    def test_strict_key_false_produces_error_in_production(
        self, strict_key: str
    ) -> None:
        config = {strict_key: False}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert any(strict_key in err for err in result.errors)

    @pytest.mark.parametrize(
        "strict_key",
        ["plugin_strict", "tool_definitions_strict", "routing_drift_strict"],
    )
    def test_strict_key_false_produces_warning_in_local(self, strict_key: str) -> None:
        config = {strict_key: False}
        result = ProductionConfigValidator().validate(config, security_profile="local")
        assert any(strict_key in warn for warn in result.warnings)

    @pytest.mark.parametrize(
        "strict_key",
        ["plugin_strict", "tool_definitions_strict", "routing_drift_strict"],
    )
    def test_strict_key_true_no_error_in_production(self, strict_key: str) -> None:
        config = {strict_key: True}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert not any(strict_key in err for err in result.errors)

    def test_all_strict_keys_true_no_errors_in_production(self) -> None:
        config = {
            "plugin_strict": True,
            "tool_definitions_strict": True,
            "routing_drift_strict": True,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert result.errors == []

    def test_all_strict_keys_absent_produces_three_errors_in_production(self) -> None:
        config: dict[str, bool] = {}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert len(result.errors) == 3

    def test_all_strict_keys_absent_produces_warnings_in_local(self) -> None:
        config: dict[str, bool] = {}
        result = ProductionConfigValidator().validate(config, security_profile="local")
        assert len(result.warnings) == 3
        assert result.errors == []


class TestProductionConfigValidatorSafetyTiers:
    """Tests for bidirectional tool_safety_tiers validation."""

    def test_missing_safety_tier_produces_error_in_production(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"shell_execute": "low"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=known_tools
        )
        assert any("'file_read'" in err for err in result.errors)

    def test_missing_safety_tier_produces_warning_in_local(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"shell_execute": "low"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="local", known_tools=known_tools
        )
        assert any("'file_read'" in warn for warn in result.warnings)

    def test_unknown_safety_tier_key_produces_error_in_production(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"unknown_tool": "high"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=known_tools
        )
        assert any("unknown_tool" in err for err in result.errors)

    def test_unknown_safety_tier_key_produces_warning_in_local(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"unknown_tool": "high"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="local", known_tools=known_tools
        )
        assert any("unknown_tool" in warn for warn in result.warnings)

    def test_both_missing_and_unknown_produce_errors_in_production(self) -> None:
        known_tools = {"shell_execute", "file_read", "github_search"}
        config = {
            "tool_safety_tiers": {"unknown_tool": "high"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=known_tools
        )
        assert any(
            "missing" in err.lower() or "'file_read'" in err for err in result.errors
        )
        assert any(
            "unknown" in err.lower() or "unknown_tool" in err for err in result.errors
        )

    def test_no_safety_tiers_config_no_tier_errors(self) -> None:
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert not any("safety tier" in err.lower() for err in result.errors)

    def test_empty_safety_tiers_dict_no_tier_errors(self) -> None:
        config: dict[str, object] = {"tool_safety_tiers": {}, "known_tools": set()}
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=set()
        )
        assert not any("safety tier" in err.lower() for err in result.errors)

    def test_all_tiers_present_no_errors(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"shell_execute": "low", "file_read": "medium"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=known_tools
        )
        assert not any("safety tier" in err.lower() for err in result.errors)


class TestProductionConfigValidatorAllowedTools:
    """Tests for allowed_tools=[] visibility check."""

    def test_allowed_tools_empty_produces_error_in_production(self) -> None:
        config: dict[str, object] = {"allowed_tools": []}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert any("allowed_tools" in err and "[]" in err for err in result.errors)

    def test_allowed_tools_empty_produces_warning_in_local(self) -> None:
        config: dict[str, object] = {"allowed_tools": []}
        result = ProductionConfigValidator().validate(config, security_profile="local")
        assert any("allowed_tools" in warn and "[]" in warn for warn in result.warnings)

    def test_allowed_tools_nonempty_no_issue(self) -> None:
        config = {"allowed_tools": ["shell_execute"]}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert not any("allowed_tools" in err for err in result.errors)
        assert not any("allowed_tools" in warn for warn in result.warnings)

    def test_allowed_tools_none_no_issue(self) -> None:
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert not any("allowed_tools" in err for err in result.errors)


class TestProductionConfigValidatorGitHubFailOpen:
    """Tests for GitHub allowed_repos_mode='fail_open' check."""

    def test_fail_open_produces_error_in_production(self) -> None:
        config = {"allowed_repos_mode": "fail_open"}
        result = ProductionConfigValidator().validate(
            config, security_profile="production", allowed_repos_mode="fail_open"
        )
        assert any("fail_open" in err for err in result.errors)

    def test_fail_open_produces_warning_in_local(self) -> None:
        config = {"allowed_repos_mode": "fail_open"}
        result = ProductionConfigValidator().validate(
            config, security_profile="local", allowed_repos_mode="fail_open"
        )
        assert any("fail_open" in warn for warn in result.warnings)

    def test_fail_closed_no_issue(self) -> None:
        config = {"allowed_repos_mode": "fail_closed"}
        result = ProductionConfigValidator().validate(
            config, security_profile="production", allowed_repos_mode="fail_closed"
        )
        assert not any("fail_open" in err for err in result.errors)

    def test_no_fail_open_param_no_issue(self) -> None:
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert not any("fail_open" in err for err in result.errors)


class TestProductionConfigValidatorSecurityProfileEnum:
    """Tests using SecurityProfile enum values."""

    def test_production_enum_produces_error(self) -> None:
        config = {"plugin_strict": False}
        result = ProductionConfigValidator().validate(
            config, security_profile=SecurityProfile.PRODUCTION
        )
        assert any("plugin_strict" in err for err in result.errors)

    def test_local_enum_produces_warning(self) -> None:
        config = {"plugin_strict": False}
        result = ProductionConfigValidator().validate(
            config, security_profile=SecurityProfile.LOCAL
        )
        assert any("plugin_strict" in warn for warn in result.warnings)


class TestProductionConfigValidatorValidateGithubFailOpen:
    """Tests for standalone validate_github_fail_open method."""

    def test_fail_open_produces_error_in_production(self) -> None:
        result = ProductionConfigValidator().validate_github_fail_open(
            "fail_open", security_profile="production"
        )
        assert any("fail_open" in err for err in result.errors)

    def test_fail_open_produces_warning_in_local(self) -> None:
        result = ProductionConfigValidator().validate_github_fail_open(
            "fail_open", security_profile="local"
        )
        assert any("fail_open" in warn for warn in result.warnings)

    def test_fail_closed_no_issue(self) -> None:
        result = ProductionConfigValidator().validate_github_fail_open(
            "fail_closed", security_profile="production"
        )
        assert result.errors == []


class TestProductionConfigValidatorValidateUnknownToolSafetyTiers:
    """Tests for standalone validate_unknown_tool_safety_tiers method."""

    def test_empty_list_returns_no_errors(self) -> None:
        result = ProductionConfigValidator().validate_unknown_tool_safety_tiers([])
        assert result.errors == []

    def test_single_unknown_key(self) -> None:
        result = ProductionConfigValidator().validate_unknown_tool_safety_tiers(["mdq"])
        assert len(result.errors) == 1
        assert "mdq" in result.errors[0]

    def test_multiple_unknown_keys(self) -> None:
        result = ProductionConfigValidator().validate_unknown_tool_safety_tiers(
            ["mdq", "unknown_tool"]
        )
        assert len(result.errors) == 2
        assert "mdq" in result.errors[0] or "mdq" in result.errors[1]
        assert "unknown_tool" in result.errors[0] or "unknown_tool" in result.errors[1]
