"""tests/mcp_servers/web_search/test_web_search_security_validation.py

Web Search self-validation for scripts/mcp_servers/web_search/web_search_models.py
(REQ-015, AC-005).

The checks are asserted on the validator output; the posture-level consequences (validated,
ready, the bind gate) are pinned in tests/mcp_servers/web_search/test_web_search_health_posture.py.
"""

from __future__ import annotations

from typing import Any

import pytest
from mcp_servers.web_search.web_search_models import (
    HARD_BROWSER_MAX_RESPONSE_KB,
    HARD_BROWSER_TIMEOUT_SEC_LIMIT,
    HARD_MAX_RESULTS_LIMIT,
    WEB_SEARCH_OWN_CONFIG_FILE,
    WebSearchConfig,
    validate_web_search_security,
)


def _statuses(cfg: WebSearchConfig) -> dict[str, tuple[str, str]]:
    """Return every check id mapped to (status, reason_code) for *cfg*."""
    return {
        check.check_id: (check.status.value, check.reason_code)
        for check in validate_web_search_security(cfg)
    }


def _cfg(**overrides: Any) -> WebSearchConfig:
    """Build a config directly, bypassing the bounds _validate_config_bounds() enforces.

    Constructing the dataclass instead of calling load() is what lets a test hold a value
    the loader would reject, which is the state the posture must report.
    """
    return WebSearchConfig(**overrides)


class TestCheckSet:
    """Row 03 requires the same check ids for every configuration."""

    def test_the_five_check_ids_appear_in_a_fixed_order(self) -> None:
        ids = [check.check_id for check in validate_web_search_security(_cfg())]

        assert ids == [
            "server.results_bounds",
            "server.search_timeout_valid",
            "server.browser_timeout_valid",
            "server.browser_response_limit",
            "server.browser_allowlist",
        ]

    def test_the_check_set_does_not_change_with_the_allowlist(self) -> None:
        empty = [check.check_id for check in validate_web_search_security(_cfg())]
        filled = [
            check.check_id
            for check in validate_web_search_security(
                _cfg(browser_allowed_domains=["example.com"])
            )
        ]

        assert empty == filled


class TestResultCountBounds:
    """server.results_bounds mirrors the rules _validate_config_bounds() enforces."""

    def test_shipped_shape_is_ok(self) -> None:
        assert _statuses(_cfg())["server.results_bounds"] == ("ok", "ok")

    def test_default_above_limit_is_a_failure(self) -> None:
        statuses = _statuses(_cfg(default_max_results=30, max_results_limit=20))

        assert statuses["server.results_bounds"] == ("failed", "config_invalid")

    def test_limit_above_the_module_ceiling_is_a_failure(self) -> None:
        statuses = _statuses(_cfg(max_results_limit=HARD_MAX_RESULTS_LIMIT + 1))

        assert statuses["server.results_bounds"] == ("failed", "config_invalid")


class TestSearchTimeout:
    """server.search_timeout_valid mirrors the search_timeout_sec rule."""

    def test_zero_is_a_failure(self) -> None:
        assert _statuses(_cfg(search_timeout_sec=0.0))[
            "server.search_timeout_valid"
        ] == (
            "failed",
            "config_invalid",
        )

    def test_above_the_ceiling_is_a_failure(self) -> None:
        statuses = _statuses(_cfg(search_timeout_sec=60.5))

        assert statuses["server.search_timeout_valid"] == ("failed", "config_invalid")


class TestBrowserTimeout:
    """server.browser_timeout_valid is the gap _validate_config_bounds() leaves open."""

    @pytest.mark.parametrize("value", [0, -1])
    def test_non_positive_is_a_failure(self, value: int) -> None:
        assert _statuses(_cfg(browser_timeout_sec=value))[
            "server.browser_timeout_valid"
        ] == (
            "failed",
            "config_invalid",
        )

    def test_above_the_ceiling_is_a_failure(self) -> None:
        statuses = _statuses(
            _cfg(browser_timeout_sec=HARD_BROWSER_TIMEOUT_SEC_LIMIT + 1)
        )

        assert statuses["server.browser_timeout_valid"] == ("failed", "config_invalid")

    def test_the_shipped_default_is_ok(self) -> None:
        assert _statuses(_cfg())["server.browser_timeout_valid"] == ("ok", "ok")


class TestBrowserResponseLimit:
    """server.browser_response_limit bounds the extracted-text cap."""

    @pytest.mark.parametrize("value", [0, -5])
    def test_non_positive_is_a_failure(self, value: int) -> None:
        statuses = _statuses(_cfg(browser_max_response_kb=value))

        assert statuses["server.browser_response_limit"] == ("failed", "config_invalid")

    def test_above_the_ceiling_is_a_failure(self) -> None:
        statuses = _statuses(
            _cfg(browser_max_response_kb=HARD_BROWSER_MAX_RESPONSE_KB + 1)
        )

        assert statuses["server.browser_response_limit"] == ("failed", "config_invalid")


class TestBrowserAllowlist:
    """An empty allowlist removes a capability, so it is never FAILED (REQ-015)."""

    def test_empty_allowlist_is_not_applicable(self) -> None:
        statuses = _statuses(_cfg(browser_allowed_domains=[]))

        assert statuses["server.browser_allowlist"] == (
            "not_applicable",
            "not_applicable",
        )

    def test_hostname_shaped_entries_are_ok(self) -> None:
        statuses = _statuses(
            _cfg(browser_allowed_domains=["example.com", "docs.python.org"])
        )

        assert statuses["server.browser_allowlist"] == ("ok", "ok")

    @pytest.mark.parametrize(
        "entry",
        [
            "Example.com",
            "https://example.com",
            "example.com/path",
            "example.com:443",
            " ",
        ],
    )
    def test_a_malformed_entry_is_a_warning_not_a_failure(self, entry: str) -> None:
        statuses = _statuses(_cfg(browser_allowed_domains=[entry]))

        assert statuses["server.browser_allowlist"] == ("warning", "allowlist_invalid")

    def test_message_reports_a_count_not_the_entry(self) -> None:
        entry = "Docs.Python.org"
        checks = validate_web_search_security(_cfg(browser_allowed_domains=[entry]))
        message = next(
            check.message
            for check in checks
            if check.check_id == "server.browser_allowlist"
        )

        assert entry not in message
        assert "1 of 1" in message


class TestNonSecretView:
    """The view row 51 exposes carries scalars, a count, and a presence flag (REQ-009)."""

    def test_view_carries_no_token_or_domain_value(self) -> None:
        cfg = _cfg(
            auth_token="super-secret-token", browser_allowed_domains=["example.com"]
        )
        view = cfg.non_secret_view()

        assert "super-secret-token" not in str(view)
        assert "example.com" not in str(view)
        assert view["browser_allowlist_count"] == 1
        assert view["auth_token_present"] is True

    def test_view_names_the_own_config_file(self) -> None:
        assert _cfg().non_secret_view()["own_config_file"] == WEB_SEARCH_OWN_CONFIG_FILE

    def test_view_carries_no_list_values(self) -> None:
        view = _cfg(browser_allowed_domains=["example.com"]).non_secret_view()

        assert not any(isinstance(value, list) for value in view.values())

    def test_view_does_not_alias_the_config_list(self) -> None:
        cfg = _cfg(browser_allowed_domains=["example.com"])
        view = cfg.non_secret_view()
        view["extra"] = 1

        assert cfg.browser_allowed_domains == ["example.com"]
