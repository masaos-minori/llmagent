"""tests/mcp_servers/web_search/test_web_search_security_validation.py

Web Search self-validation for scripts/mcp_servers/web_search/web_search_security_checks.py
(REQ-015, AC-005), whose checks read the WebSearchConfig defined in web_search_models.py.

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
    HARD_SEARCH_TIMEOUT_SEC_LIMIT,
    WEB_SEARCH_OWN_CONFIG_FILE,
    WebSearchConfig,
)
from mcp_servers.web_search.web_search_security_checks import (
    _is_hostname_shape,
    validate_web_search_security,
)


def _statuses(cfg: WebSearchConfig) -> dict[str, tuple[str, str]]:
    """Return every check id mapped to (status, reason_code) for *cfg*."""
    return {
        check.check_id: (check.status.value, check.reason_code)
        for check in validate_web_search_security(cfg)
    }


def _message(cfg: WebSearchConfig, check_id: str) -> str:
    """Return the exact message text *cfg* produces for *check_id*."""
    return next(
        check.message
        for check in validate_web_search_security(cfg)
        if check.check_id == check_id
    )


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
    """server.browser_timeout_valid reports the bound _validate_config_bounds() rejects."""

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


# ── Characterization tests for the paths the suite left unpinned ──────────────
#
# These lock the exact message text and the remaining boundary values the refactor
# of validate_web_search_security() must preserve.


class TestBoundsRuleConjunction:
    """bounds_ok is a conjunction of four rules; each one alone can fail it."""

    @pytest.mark.parametrize(
        "overrides",
        [
            {"default_max_results": 0},
            {"default_max_results": -3},
            {"max_results_limit": 0},
            {"max_results_limit": -1},
            {"default_max_results": 30, "max_results_limit": 20},
            {"max_results_limit": HARD_MAX_RESULTS_LIMIT + 1},
        ],
    )
    def test_each_rule_violation_fails_the_check(
        self, overrides: dict[str, int]
    ) -> None:
        assert _statuses(_cfg(**overrides))["server.results_bounds"] == (
            "failed",
            "config_invalid",
        )

    def test_the_module_ceiling_itself_is_ok(self) -> None:
        statuses = _statuses(
            _cfg(default_max_results=1, max_results_limit=HARD_MAX_RESULTS_LIMIT)
        )

        assert statuses["server.results_bounds"] == ("ok", "ok")


class TestTimeoutAndSizeCeilings:
    """The ceilings are inclusive and the lower bounds are exclusive."""

    @pytest.mark.parametrize("value", [0.0, -0.5])
    def test_non_positive_search_timeout_is_a_failure(self, value: float) -> None:
        assert _statuses(_cfg(search_timeout_sec=value))[
            "server.search_timeout_valid"
        ] == (
            "failed",
            "config_invalid",
        )

    def test_exactly_the_ceiling_is_ok(self) -> None:
        statuses = _statuses(_cfg(search_timeout_sec=HARD_SEARCH_TIMEOUT_SEC_LIMIT))

        assert statuses["server.search_timeout_valid"] == ("ok", "ok")

    def test_exactly_the_browser_ceiling_is_ok(self) -> None:
        statuses = _statuses(
            _cfg(
                browser_timeout_sec=HARD_BROWSER_TIMEOUT_SEC_LIMIT,
                browser_max_response_kb=HARD_BROWSER_MAX_RESPONSE_KB,
            )
        )

        assert statuses["server.browser_timeout_valid"] == ("ok", "ok")
        assert statuses["server.browser_response_limit"] == ("ok", "ok")


class TestHostnameShape:
    """_is_hostname_shape() is the posture-time mirror of _check_domain()'s comparison."""

    @pytest.mark.parametrize("value", ["", " ", "\t"])
    def test_blank_entries_are_not_hostname_shaped(self, value: str) -> None:
        assert _is_hostname_shape(value) is False

    @pytest.mark.parametrize(
        "entry",
        ["Example.com", "https://example.com", "example.com/path", "example.com:443"],
    )
    def test_scheme_path_port_and_case_are_rejected(self, entry: str) -> None:
        assert _is_hostname_shape(entry) is False

    @pytest.mark.parametrize("entry", ["example.com", "docs.python.org", "localhost"])
    def test_plain_lowercase_hostnames_are_accepted(self, entry: str) -> None:
        assert _is_hostname_shape(entry) is True


class TestCheckMessages:
    """Every message names the setting and its state; allowlist entries stay by count."""

    def test_results_bounds_messages(self) -> None:
        assert _message(_cfg(), "server.results_bounds") == (
            "default_max_results is within max_results_limit and the module ceiling"
        )
        assert _message(_cfg(default_max_results=0), "server.results_bounds") == (
            "result-count bounds are violated so the advertised inputSchema is not enforced"
        )

    def test_search_timeout_messages(self) -> None:
        assert _message(_cfg(), "server.search_timeout_valid") == (
            "search_timeout_sec is in (0, HARD_SEARCH_TIMEOUT_SEC_LIMIT]"
        )
        assert _message(
            _cfg(search_timeout_sec=0.0), "server.search_timeout_valid"
        ) == ("search_timeout_sec is outside (0, HARD_SEARCH_TIMEOUT_SEC_LIMIT]")

    def test_browser_timeout_messages(self) -> None:
        assert _message(_cfg(), "server.browser_timeout_valid") == (
            "browser_timeout_sec is in (0, HARD_BROWSER_TIMEOUT_SEC_LIMIT]"
        )
        assert _message(
            _cfg(browser_timeout_sec=0), "server.browser_timeout_valid"
        ) == (
            "browser_timeout_sec must be positive and within HARD_BROWSER_TIMEOUT_SEC_LIMIT"
        )

    def test_browser_response_limit_messages(self) -> None:
        assert _message(_cfg(), "server.browser_response_limit") == (
            "browser_max_response_kb is positive and within HARD_BROWSER_MAX_RESPONSE_KB"
        )
        assert _message(
            _cfg(browser_max_response_kb=0), "server.browser_response_limit"
        ) == (
            "browser_max_response_kb must be positive and within HARD_BROWSER_MAX_RESPONSE_KB"
        )

    def test_allowlist_messages(self) -> None:
        assert _message(
            _cfg(browser_allowed_domains=[]), "server.browser_allowlist"
        ) == (
            "browser_allowed_domains is empty so browser_fetch is disabled for every domain"
        )
        assert _message(
            _cfg(browser_allowed_domains=["example.com", "docs.python.org"]),
            "server.browser_allowlist",
        ) == ("browser_allowed_domains holds 2 hostname-shaped entries")
        assert _message(
            _cfg(
                browser_allowed_domains=[
                    "example.com",
                    "Docs.Python.org",
                    "https://x.com",
                ]
            ),
            "server.browser_allowlist",
        ) == (
            "browser_allowed_domains contains 2 of 3 entries that cannot match a hostname"
        )

    def test_no_message_carries_a_configured_value(self) -> None:
        cfg = _cfg(
            default_max_results=7,
            max_results_limit=9,
            search_timeout_sec=11.5,
            browser_timeout_sec=13,
            browser_max_response_kb=17,
            browser_allowed_domains=["private-intranet.example"],
            auth_token="super-secret-token",
        )

        rendered = " | ".join(
            check.message for check in validate_web_search_security(cfg)
        )
        for value in (
            "7",
            "9",
            "11.5",
            "13",
            "17",
            "private-intranet.example",
            "super-secret-token",
        ):
            assert value not in rendered
