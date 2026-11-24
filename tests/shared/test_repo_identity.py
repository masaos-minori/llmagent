"""Tests for scripts/shared/repo_identity.py.

Covers the contract of the two shared helpers (REQ-002, REQ-010):
1. normalize_repo_key: mixed-case input yields the canonical lowercase key.
2. normalize_repo_key: already-canonical input is returned unchanged.
3. normalize_repo_key: non-string input is rejected with ValueError.
4. is_canonical_repo_key: shape and case cases for a stored allowlist entry.
"""

import pytest
from shared.repo_identity import is_canonical_repo_key, normalize_repo_key


class TestNormalizeRepoKey:
    def test_mixed_case_input_yields_canonical_key(self) -> None:
        assert normalize_repo_key("Owner", "Repo") == "owner/repo"

    def test_mixed_case_owner_only_yields_canonical_key(self) -> None:
        assert normalize_repo_key("OpenAI", "Codex") == "openai/codex"

    def test_already_canonical_input_is_unchanged(self) -> None:
        assert normalize_repo_key("owner", "repo") == "owner/repo"

    def test_non_string_owner_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="repo identity parts must be str"):
            normalize_repo_key(None, "repo")

    def test_non_string_repo_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="repo identity parts must be str"):
            normalize_repo_key("owner", 1)


class TestIsCanonicalRepoKey:
    @pytest.mark.parametrize(
        "entry",
        ["owner/repo", "openai/codex", "owner-1/repo_2", "12345/repo"],
    )
    def test_canonical_entries_are_accepted(self, entry: str) -> None:
        assert is_canonical_repo_key(entry) is True

    @pytest.mark.parametrize(
        "entry",
        [
            "Owner/repo",
            "owner/Repo",
            "OWNER/REPO",
            "owner",
            "owner/",
            "/repo",
            "",
            "a/b/c",
            "not/a/repo/key",
        ],
    )
    def test_non_canonical_entries_are_rejected(self, entry: str) -> None:
        assert is_canonical_repo_key(entry) is False

    def test_non_string_entry_is_rejected(self) -> None:
        assert is_canonical_repo_key(None) is False

    def test_helper_does_not_modify_the_entry(self) -> None:
        entry = "Owner/repo"
        is_canonical_repo_key(entry)
        assert entry == "Owner/repo"
