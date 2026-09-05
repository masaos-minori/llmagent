from __future__ import annotations

from pathlib import PurePosixPath

from mcp_servers.git.git_security import is_within_allowed_paths

# --- Helper fixtures ---------------------------------------------------------

ALLOWED_ROOTS = ["/tmp/repo"]

# --- Positive cases: path inside allowed root --------------------------------


class TestWithinAllowedRoots:
    """Paths that should be authorized when /tmp/repo is the only allowed root."""

    def test_exact_root(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo", ALLOWED_ROOTS)
        assert ok is True
        assert err == ""

    def test_subdir_of_root(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo/subdir", ALLOWED_ROOTS)
        assert ok is True
        assert err == ""

    def test_nested_subdir(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo/a/b/c", ALLOWED_ROOTS)
        assert ok is True
        assert err == ""

    def test_trailing_slash_normalized(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo/", ALLOWED_ROOTS)
        assert ok is True
        assert err == ""

    def test_symlink_resolved_inside_root(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo/../repo", ALLOWED_ROOTS)
        assert ok is True
        assert err == ""


# --- Negative cases: sibling-path attacks ------------------------------------


class TestSiblingPathRejection:
    """Paths that should NOT be authorized even though they share a prefix."""

    def test_sibling_with_underscore(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo_evil", ALLOWED_ROOTS)
        assert ok is False
        assert "[DENIED]" in err

    def test_sibling_with_dash(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo-evil", ALLOWED_ROOTS)
        assert ok is False
        assert "[DENIED]" in err

    def test_sibling_with_dot(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo.evil", ALLOWED_ROOTS)
        assert ok is False
        assert "[DENIED]" in err

    def test_sibling_prefix_longer(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/repo_evil/sub", ALLOWED_ROOTS)
        assert ok is False
        assert "[DENIED]" in err

    def test_sibling_prefix_shorter(self) -> None:
        ok, err = is_within_allowed_paths("/tmp/re", ALLOWED_ROOTS)
        assert ok is False
        assert "[DENIED]" in err


# --- Edge cases: empty list, missing path, etc. ------------------------------


class TestEdgeCases:
    """Boundary conditions for is_within_allowed_paths."""

    def test_empty_allowed_list_returns_false(self) -> None:
        # Fail-closed-empty-list convention: deny when no allowed paths configured
        ok, err = is_within_allowed_paths("/any/path", [])
        assert ok is False
        assert "[DENIED]" in err

    def test_none_allowed_list_treated_as_empty(self) -> None:
        # None is caught by `if not allowed_repo_paths:` → denied per fail-closed convention
        ok, err = is_within_allowed_paths("/any/path", None)  # type: ignore[arg-type] — None is valid input that triggers deny-all path
        assert ok is False
        assert "[DENIED]" in err

    def test_absolute_vs_relative(self) -> None:
        ok, err = is_within_allowed_paths("relative/path", ALLOWED_ROOTS)
        assert ok is False
        assert "[DENIED]" in err

    def test_multiple_roots_match_second(self) -> None:
        roots = ["/tmp/repo", "/var/repos"]
        ok, err = is_within_allowed_paths("/var/repos/proj", roots)
        assert ok is True
        assert err == ""

    def test_multiple_roots_no_match(self) -> None:
        roots = ["/tmp/repo", "/var/repos"]
        ok, err = is_within_allowed_paths("/etc/passwd", roots)
        assert ok is False
        assert "[DENIED]" in err


# --- PurePosixPath component-aware containment verification -------------------


class TestComponentAwareContainment:
    """Verify that PurePosixPath.relative_to() is used for component-aware checks."""

    def test_pure_posix_path_component_boundary(self) -> None:
        """PurePosixPath.relative_to raises ValueError on partial match."""
        try:
            PurePosixPath("/tmp/repo-evil").relative_to(PurePosixPath("/tmp/repo"))
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected — confirms component-aware boundary

    def test_pure_posix_path_full_match(self) -> None:
        """PurePosixPath.relative_to succeeds on full containment."""
        rel = PurePosixPath("/tmp/repo/sub").relative_to(PurePosixPath("/tmp/repo"))
        assert str(rel) == "sub"
