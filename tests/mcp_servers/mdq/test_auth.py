"""tests/mcp_servers/mdq/test_auth.py

Direct characterization tests for `mcp_servers.mdq.auth.authorize_path` —
the fail-closed allowlist check underlying MDQ path authorization.

Complements the integration-level coverage in `test_mdq_path_jail.py` and
`test_mdq_read_authorization.py` (which exercise this function indirectly via
`MdqService`/`index_paths`) by covering the function's own boundary and error
paths directly, including the `Path.resolve()` failure branches that are hard
to trigger through the filesystem alone.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from mcp_servers.mdq.auth import authorize_path


class TestAuthorizePathAllowlist:
    def test_empty_allowlist_denies(self, tmp_path: Path) -> None:
        """An empty allowlist fails closed (denies all paths)."""
        assert authorize_path(tmp_path / "f.md", []) is False

    def test_path_within_allowed_dir_is_authorized(self, tmp_path: Path) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        target = allowed / "file.md"
        target.write_text("content", encoding="utf-8")

        assert authorize_path(target, [str(allowed)]) is True

    def test_path_equal_to_allowed_dir_is_authorized(self, tmp_path: Path) -> None:
        """The allowed directory itself (not just its contents) is authorized."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()

        assert authorize_path(allowed, [str(allowed)]) is True

    def test_path_outside_allowed_dirs_is_denied(self, tmp_path: Path) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside = tmp_path / "outside" / "file.md"

        assert authorize_path(outside, [str(allowed)]) is False

    def test_matches_second_of_multiple_allowed_dirs(self, tmp_path: Path) -> None:
        first = tmp_path / "first"
        first.mkdir()
        second = tmp_path / "second"
        second.mkdir()
        target = second / "file.md"

        assert authorize_path(target, [str(first), str(second)]) is True

    def test_sibling_dir_sharing_a_name_prefix_is_not_authorized(
        self, tmp_path: Path
    ) -> None:
        """A sibling dir like 'allowed-other' must not satisfy allowlist 'allowed'."""
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        sibling = tmp_path / "allowed-other" / "file.md"

        assert authorize_path(sibling, [str(allowed)]) is False

    def test_symlink_escape_is_denied(self, tmp_path: Path) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        outside_target = tmp_path / "outside.md"
        outside_target.write_text("secret", encoding="utf-8")
        link = allowed / "escape.md"
        link.symlink_to(outside_target)

        assert authorize_path(link, [str(allowed)]) is False


class TestAuthorizePathExceptionHandling:
    """Covers the two fail-closed except branches around `Path.resolve()`."""

    def test_target_path_resolve_failure_denies(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        allowed = tmp_path / "allowed"
        allowed.mkdir()
        target = tmp_path / "target.md"
        original_resolve = Path.resolve

        def fake_resolve(self: Path, *args: object, **kwargs: object) -> Path:
            if self == target:
                raise OSError("simulated resolve failure")
            return original_resolve(self, *args, **kwargs)  # type: ignore[arg-type] — unbound method call via captured Path.resolve, valid at runtime but untyped by mypy

        monkeypatch.setattr(Path, "resolve", fake_resolve)

        assert authorize_path(target, [str(allowed)]) is False

    def test_one_allowed_dir_resolve_failure_is_skipped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A root that fails to resolve is skipped; later roots are still checked."""
        bad_root = tmp_path / "bad_root"
        good_root = tmp_path / "good_root"
        good_root.mkdir()
        target = good_root / "file.md"
        original_resolve = Path.resolve

        def fake_resolve(self: Path, *args: object, **kwargs: object) -> Path:
            if self == bad_root:
                raise ValueError("simulated resolve failure")
            return original_resolve(self, *args, **kwargs)  # type: ignore[arg-type] — unbound method call via captured Path.resolve, valid at runtime but untyped by mypy

        monkeypatch.setattr(Path, "resolve", fake_resolve)

        assert authorize_path(target, [str(bad_root), str(good_root)]) is True
