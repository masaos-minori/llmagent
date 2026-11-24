"""
tests/mcp_servers/github/test_github_config_strict_parsing.py

T-04 regression coverage for strict, fail-fast GitHub config parsing (mcpai003
REQ-006 shared strict config helpers, REQ-007 shared `owner/repo` identity).

`from_dict` parses and normalizes; `load` decides whether the parsed config may
start the server. Both boundaries are asserted here.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from mcp_servers.github.github_models_config import GitHubConfig

_REPO = Path(__file__).resolve().parents[3]
_AUTH_ENV_VAR = "MCP_GITHUB_AUTH_TOKEN"

# A config that satisfies every startup rule; individual tests break one key.
_BASE_CONFIG = {
    "allowed_repos": ["org/repo"],
    "protected_branches": ["main"],
    "max_per_page": 100,
}


def _patch_loader(monkeypatch: pytest.MonkeyPatch, raw: dict) -> None:
    class _FakeLoader:
        def load(self, name: str) -> dict:
            return raw

    monkeypatch.setattr(
        "mcp_servers.github.github_models_config.ConfigLoader", _FakeLoader
    )


# ── strict booleans (REQ-006) ────────────────────────────────────────────────


class TestStrictBooleans:
    def test_string_false_for_allow_force_push_is_rejected(self) -> None:
        """`bool("false")` is True: the old coercion silently enabled force push."""
        with pytest.raises(ValueError, match="allow_force_push"):
            GitHubConfig.from_dict({"allow_force_push": "false"})

    def test_string_zero_for_require_pr_review_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="require_pr_review"):
            GitHubConfig.from_dict({"require_pr_review": "0"})

    def test_integer_for_boolean_key_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="allow_global_search"):
            GitHubConfig.from_dict({"allow_global_search": 1})

    def test_real_booleans_are_kept(self) -> None:
        cfg = GitHubConfig.from_dict(
            {"allow_force_push": True, "require_pr_review": False}
        )
        assert cfg.allow_force_push is True
        assert cfg.require_pr_review is False

    def test_absent_keys_keep_the_documented_defaults(self) -> None:
        cfg = GitHubConfig.from_dict({})
        assert cfg.allow_force_push is False
        assert cfg.require_pr_review is True


# ── numeric limits: finite, non-negative (REQ-006) ───────────────────────────


class TestNumericLimits:
    @pytest.mark.parametrize("key", ["max_file_size_kb", "max_file_read_size_kb"])
    @pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True])
    def test_from_dict_rejects_invalid_size_limits(
        self, key: str, value: object
    ) -> None:
        with pytest.raises(ValueError, match=key):
            GitHubConfig.from_dict({key: value})

    @pytest.mark.parametrize("key", ["max_file_size_kb", "max_file_read_size_kb"])
    def test_zero_size_limit_stays_the_no_limit_convention(self, key: str) -> None:
        cfg = GitHubConfig.from_dict({key: 0})
        assert getattr(cfg, key) == 0

    @pytest.mark.parametrize("key", ["default_per_page", "max_per_page"])
    @pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True])
    def test_from_dict_rejects_invalid_pagination_limits(
        self, key: str, value: object
    ) -> None:
        with pytest.raises(ValueError, match=key):
            GitHubConfig.from_dict({key: value})

    @pytest.mark.parametrize("key", ["default_per_page", "max_per_page"])
    def test_load_rejects_zero_pagination_limit(
        self, monkeypatch: pytest.MonkeyPatch, key: str
    ) -> None:
        """`0` parses (shared helper 'no limit' convention) but must not start the server."""
        _patch_loader(monkeypatch, {**_BASE_CONFIG, key: 0})
        with pytest.raises(ValueError, match="greater than 0"):
            GitHubConfig.load()

    def test_load_rejects_default_per_page_above_max(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_loader(
            monkeypatch, {**_BASE_CONFIG, "default_per_page": 50, "max_per_page": 10}
        )
        with pytest.raises(ValueError, match="must not exceed max_per_page"):
            GitHubConfig.load()

    def test_load_accepts_a_consistent_pagination_pair(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_loader(
            monkeypatch, {**_BASE_CONFIG, "default_per_page": 10, "max_per_page": 10}
        )
        cfg = GitHubConfig.load()
        assert cfg.default_per_page == 10
        assert cfg.max_per_page == 10


# ── allowed_repos identity (REQ-007) ─────────────────────────────────────────


class TestAllowedRepoIdentity:
    def test_from_dict_canonicalizes_and_deduplicates_in_sorted_order(self) -> None:
        cfg = GitHubConfig.from_dict(
            {"allowed_repos": ["Other/Repo", "other/repo", "a/b", "A/B"]}
        )
        assert cfg.allowed_repos == ["a/b", "other/repo"]

    def test_deduplication_is_order_independent(self) -> None:
        first = GitHubConfig.from_dict({"allowed_repos": ["b/x", "a/y", "A/Y"]})
        second = GitHubConfig.from_dict({"allowed_repos": ["A/Y", "b/x", "a/y"]})
        assert first.allowed_repos == second.allowed_repos == ["a/y", "b/x"]

    def test_from_dict_keeps_malformed_entries_visible_without_crashing(self) -> None:
        cfg = GitHubConfig.from_dict({"allowed_repos": ["owner/", "a/b/c", 123]})
        assert cfg.allowed_repos == ["owner/", "a/b/c", 123]

    @pytest.mark.parametrize("entry", ["owner/", "/repo", "a/b/c", 123])
    def test_load_rejects_non_canonical_entries(
        self, monkeypatch: pytest.MonkeyPatch, entry: object
    ) -> None:
        _patch_loader(monkeypatch, {**_BASE_CONFIG, "allowed_repos": [entry]})
        with pytest.raises(ValueError, match="allowed_repos"):
            GitHubConfig.load()

    def test_load_accepts_canonical_entries(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _patch_loader(monkeypatch, {**_BASE_CONFIG, "allowed_repos": ["a/b", "c/d"]})
        cfg = GitHubConfig.load()
        assert cfg.allowed_repos == ["a/b", "c/d"]

    def test_load_accepts_entries_normalized_by_from_dict(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Upper-case entries are rewritten at parse time, so startup sees one identity."""
        _patch_loader(
            monkeypatch, {**_BASE_CONFIG, "allowed_repos": ["Owner/Repo", "owner/repo"]}
        )
        cfg = GitHubConfig.load()
        assert cfg.allowed_repos == ["owner/repo"]

    def test_empty_allowlist_stays_loadable(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Fail-closed at runtime (deny all) is not a startup error."""
        _patch_loader(monkeypatch, {**_BASE_CONFIG, "allowed_repos": []})
        assert GitHubConfig.load().allowed_repos == []


# ── shipped config regression ────────────────────────────────────────────────


class TestShippedConfigStillLoads:
    def test_load_accepts_config_github_mcp_server_toml(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The deployed config satisfies every new startup rule."""
        monkeypatch.setenv(_AUTH_ENV_VAR, "test-token")
        raw = tomllib.loads(
            (_REPO / "config" / "github_mcp_server.toml").read_text(encoding="utf-8")
        )
        _patch_loader(monkeypatch, raw)
        cfg = GitHubConfig.load()
        assert cfg.protected_branches
        assert cfg.max_per_page == 100
        assert cfg.default_per_page <= cfg.max_per_page
        assert cfg.allowed_repos == sorted(cfg.allowed_repos)
