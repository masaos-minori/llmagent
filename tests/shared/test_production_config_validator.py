from __future__ import annotations

import pytest
from shared.mcp_config import SecurityProfile
from shared.production_config_validator import ProductionConfigValidator


class TestProductionConfigValidatorStrictKeys:
    """Tests for strict key validation (tool_definitions_strict, routing_drift_strict)."""

    @pytest.mark.parametrize(
        "strict_key",
        ["tool_definitions_strict", "routing_drift_strict"],
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
        ["tool_definitions_strict", "routing_drift_strict"],
    )
    def test_strict_key_false_produces_error_even_with_local_profile(
        self, strict_key: str
    ) -> None:
        config = {strict_key: False}
        result = ProductionConfigValidator().validate(config, security_profile="local")
        assert any(strict_key in err for err in result.errors)
        assert result.warnings == []

    @pytest.mark.parametrize(
        "strict_key",
        ["tool_definitions_strict", "routing_drift_strict"],
    )
    def test_strict_key_true_no_error_in_production(self, strict_key: str) -> None:
        config = {strict_key: True}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert not any(strict_key in err for err in result.errors)

    def test_all_strict_keys_true_no_errors_in_production(self) -> None:
        config = {
            "tool_definitions_strict": True,
            "routing_drift_strict": True,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert result.errors == []

    def test_all_strict_keys_absent_produces_two_errors_in_production(self) -> None:
        config: dict[str, bool] = {}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
        )
        assert len(result.errors) == 2

    def test_all_strict_keys_absent_produces_errors_even_with_local_profile(
        self,
    ) -> None:
        config: dict[str, bool] = {}
        result = ProductionConfigValidator().validate(config, security_profile="local")
        assert len(result.errors) == 2
        assert result.warnings == []


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

    def test_missing_safety_tier_produces_error_even_with_local_profile(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"shell_execute": "low"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="local", known_tools=known_tools
        )
        assert any("'file_read'" in err for err in result.errors)
        assert result.warnings == []

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

    def test_unknown_safety_tier_key_produces_error_even_with_local_profile(
        self,
    ) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"unknown_tool": "high"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="local", known_tools=known_tools
        )
        assert any("unknown_tool" in err for err in result.errors)
        assert result.warnings == []

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


class TestProductionConfigValidatorRegistryLookupFallback:
    """Tests for the best-effort tool registry lookup fallback (known_tools=None)."""

    def test_registry_lookup_failure_skips_tool_safety_tier_checks(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When resolving known_tools from the registry raises, both the missing-
        and unknown-tier checks are skipped (best-effort) rather than propagating."""

        def _raise() -> None:
            raise RuntimeError("registry unavailable")

        monkeypatch.setattr("shared.tool_registry.get_registry", _raise)
        config = {"tool_safety_tiers": {"mystery_tool": "low"}}
        result = ProductionConfigValidator().validate(
            config, security_profile="production"
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

    def test_allowed_tools_empty_produces_error_even_with_local_profile(self) -> None:
        config: dict[str, object] = {"allowed_tools": []}
        result = ProductionConfigValidator().validate(config, security_profile="local")
        assert any("allowed_tools" in err and "[]" in err for err in result.errors)
        assert result.warnings == []

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


class TestProductionConfigValidatorSecurityProfileEnum:
    """Tests using SecurityProfile enum values."""

    def test_production_enum_produces_error(self) -> None:
        config = {"tool_definitions_strict": False}
        result = ProductionConfigValidator().validate(
            config, security_profile=SecurityProfile.PRODUCTION
        )
        assert any("tool_definitions_strict" in err for err in result.errors)
        assert result.warnings == []


class TestProductionConfigValidatorApprovalRiskFloor:
    """Tests for the git write-tool approval risk floor check (REQ-001)."""

    GIT_TOOLS = {"git_checkout", "git_pull", "git_push"}

    def test_all_git_tools_high_no_issue(self) -> None:
        config = {
            "approval_risk_rules": {
                "git_checkout": "high",
                "git_pull": "high",
                "git_push": "high",
            },
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=self.GIT_TOOLS
        )
        assert not any("Effective risk below HIGH" in err for err in result.errors)

    def test_one_git_tool_medium_produces_error_in_production(self) -> None:
        config = {
            "approval_risk_rules": {
                "git_checkout": "medium",
                "git_pull": "high",
                "git_push": "high",
            },
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )

    def test_one_git_tool_medium_produces_error_even_with_local_profile(self) -> None:
        config = {
            "approval_risk_rules": {
                "git_checkout": "medium",
                "git_pull": "high",
                "git_push": "high",
            },
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="local", known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )
        assert result.warnings == []

    def test_one_git_tool_invalid_value_produces_error_in_production(self) -> None:
        """'low' is not a valid RiskLevel — classify_risk() would raise ValueError
        at call time in production, so the floor check must flag it rather than
        silently skip it."""
        config = {
            "approval_risk_rules": {
                "git_checkout": "low",
                "git_pull": "high",
                "git_push": "high",
            },
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )

    def test_git_tool_absent_from_rules_falls_back_to_tier_default(self) -> None:
        """No approval_risk_rules entry but tool_safety_tiers=WRITE_DANGEROUS
        implicitly resolves to MEDIUM and must still be flagged."""
        config = {
            "approval_risk_rules": {"git_pull": "high", "git_push": "high"},
            "tool_safety_tiers": {"git_checkout": "WRITE_DANGEROUS"},
        }
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )

    def test_git_tools_absent_from_both_no_issue(self) -> None:
        """No override anywhere: classify_risk()'s UNKNOWN path treats this as
        HIGH, so the floor check must not flag it."""
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=self.GIT_TOOLS
        )
        assert not any("Effective risk below HIGH" in err for err in result.errors)

    def test_approval_risk_rules_absent_still_checks_tier_fallback(self) -> None:
        """The floor check must run even when approval_risk_rules is entirely
        absent from config, not only when it is an empty/partial Mapping."""
        config = {"tool_safety_tiers": {"git_checkout": "WRITE_DANGEROUS"}}
        result = ProductionConfigValidator().validate(
            config, security_profile="production", known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )


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
