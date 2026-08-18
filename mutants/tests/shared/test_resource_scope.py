"""tests/shared/test_resource_scope.py
Unit tests for resource_scope: scope-kind resolution, the scope-overlap conflict
predicate, and the schema-2.0 contract validator.
"""

from __future__ import annotations

from typing import Any

from shared.resource_scope import (
    _scopes_conflict,
    resolve_resource_scopes,
    validate_tool_schema_v2,
)
from shared.runtime_tool import RuntimeTool, build_runtime_tool


def _tool(**overrides: Any) -> RuntimeTool:
    """Build a RuntimeTool fixture, terse for scope-resolution tests."""
    overrides.setdefault("name", "t")
    overrides.setdefault("server_key", "s")
    return build_runtime_tool(**overrides)


class TestResolveResourceScopes:
    def test_filesystem_exact_match_resolves_single_scope(self) -> None:
        tool = _tool(
            resource_scope_kind="filesystem",
            resource_scope_keys=("path",),
            is_write=True,
        )
        result = resolve_resource_scopes(tool, {"path": "/data/a.txt"})
        assert result == ("filesystem:/data/a.txt",)

    def test_filesystem_ancestor_descendant_pair_resolves_distinct_scopes(self) -> None:
        tool = _tool(
            resource_scope_kind="filesystem",
            resource_scope_keys=("path",),
            is_write=True,
        )
        ancestor = resolve_resource_scopes(tool, {"path": "/data"})
        descendant = resolve_resource_scopes(tool, {"path": "/data/a.txt"})
        assert ancestor == ("filesystem:/data",)
        assert descendant == ("filesystem:/data/a.txt",)
        assert ancestor != descendant

    def test_move_file_resolves_dual_source_destination_scopes(self) -> None:
        tool = _tool(
            resource_scope_kind="filesystem",
            resource_scope_keys=("source", "destination"),
            is_write=True,
        )
        result = resolve_resource_scopes(
            tool, {"source": "/a/x.txt", "destination": "/b/y.txt"}
        )
        assert result == ("filesystem:/a/x.txt", "filesystem:/b/y.txt")

    def test_git_repo_same_and_different_repo_paths_resolve_distinct_scopes(
        self,
    ) -> None:
        tool = _tool(
            resource_scope_kind="git_repo",
            resource_scope_keys=("repo_path",),
            is_write=True,
        )
        same_a = resolve_resource_scopes(tool, {"repo_path": "/repos/x"})
        same_b = resolve_resource_scopes(tool, {"repo_path": "/repos/x"})
        different = resolve_resource_scopes(tool, {"repo_path": "/repos/y"})
        assert same_a == same_b
        assert same_a != different

    def test_github_repo_scope_composes_owner_and_repo(self) -> None:
        tool = _tool(
            resource_scope_kind="github_repo",
            resource_scope_keys=("owner", "repo"),
            is_write=True,
        )
        result = resolve_resource_scopes(tool, {"owner": "org", "repo": "name"})
        assert "github_repo:org/name" in result

    def test_cicd_workflow_scope_composes_repo_workflow_ref(self) -> None:
        tool = _tool(
            resource_scope_kind="cicd_workflow",
            resource_scope_keys=("repo", "workflow", "ref"),
            is_write=True,
        )
        result = resolve_resource_scopes(
            tool, {"repo": "org/repo", "workflow": "ci.yml", "ref": "main"}
        )
        assert result == ("cicd_workflow:org/repo:ci.yml:main",)

    def test_rag_store_resolves_fixed_scope(self) -> None:
        tool = _tool(
            resource_scope_kind="rag_store",
            resource_scope_keys=("store",),
            is_write=True,
        )
        result = resolve_resource_scopes(tool, {"store": "default"})
        assert result == ("rag_store:default",)

    def test_mdq_store_resolves_fixed_scope(self) -> None:
        tool = _tool(
            resource_scope_kind="mdq_store",
            resource_scope_keys=("store",),
            is_write=True,
        )
        result = resolve_resource_scopes(tool, {"store": "default"})
        assert result == ("mdq_store:default",)

    def test_shell_fixed_process_scope_ignores_args(self) -> None:
        tool = _tool(
            resource_scope_kind="process",
            resource_scope_keys=("scope",),
            is_write=True,
        )
        result = resolve_resource_scopes(tool, {"scope": "global"})
        assert result == ("process:global",)

    def test_unscoped_read_returns_empty_tuple(self) -> None:
        tool = _tool(resource_scope_kind="", is_write=False)
        result = resolve_resource_scopes(tool, {"anything": "value"})
        assert result == ()

    def test_known_write_tool_with_unresolvable_scope_falls_back_to_global_write(
        self,
    ) -> None:
        tool = _tool(
            name="delete_file",
            resource_scope_kind="filesystem",
            resource_scope_keys=("path",),
            is_write=True,
        )
        result = resolve_resource_scopes(tool, {})
        assert result == ("global:write",)
        assert all("delete_file" not in scope for scope in result)


class TestScopesConflict:
    def test_identical_scope_strings_conflict(self) -> None:
        assert _scopes_conflict("filesystem:/a", "filesystem:/a") is True

    def test_different_kind_prefixes_never_conflict_even_with_same_suffix(self) -> None:
        assert _scopes_conflict("filesystem:/a", "git_repo:/a") is False

    def test_filesystem_descendant_path_conflicts_with_ancestor(self) -> None:
        assert _scopes_conflict("filesystem:/data", "filesystem:/data/a.txt") is True
        assert _scopes_conflict("filesystem:/data/a.txt", "filesystem:/data") is True

    def test_filesystem_unrelated_siblings_do_not_conflict(self) -> None:
        assert _scopes_conflict("filesystem:/data/a", "filesystem:/data/b") is False

    def test_non_filesystem_equal_kind_different_value_does_not_conflict(self) -> None:
        assert _scopes_conflict("git_repo:/x", "git_repo:/y") is False


class TestValidateToolSchemaV2:
    def _valid_entry(self) -> dict[str, Any]:
        return {
            "name": "delete_file",
            "inputSchema": {"properties": {"path": {"type": "string"}}},
            "is_write": True,
            "requires_serial": True,
            "resource_scope_kind": "filesystem",
            "resource_scope_keys": ["path"],
        }

    def test_accepts_fully_declared_entry(self) -> None:
        assert validate_tool_schema_v2(self._valid_entry()) == []

    def test_rejects_missing_name(self) -> None:
        entry = self._valid_entry()
        del entry["name"]
        problems = validate_tool_schema_v2(entry)
        assert any("name" in p for p in problems)

    def test_rejects_missing_or_invalid_input_schema(self) -> None:
        entry = self._valid_entry()
        entry["inputSchema"] = {}
        problems = validate_tool_schema_v2(entry)
        assert any("inputSchema" in p for p in problems)

    def test_rejects_missing_is_write(self) -> None:
        entry = self._valid_entry()
        del entry["is_write"]
        problems = validate_tool_schema_v2(entry)
        assert any("is_write" in p for p in problems)

    def test_rejects_non_bool_is_write(self) -> None:
        entry = self._valid_entry()
        entry["is_write"] = 1
        problems = validate_tool_schema_v2(entry)
        assert any("is_write" in p for p in problems)

    def test_rejects_missing_requires_serial(self) -> None:
        entry = self._valid_entry()
        del entry["requires_serial"]
        problems = validate_tool_schema_v2(entry)
        assert any("requires_serial" in p for p in problems)

    def test_rejects_non_bool_requires_serial(self) -> None:
        entry = self._valid_entry()
        entry["requires_serial"] = "yes"
        problems = validate_tool_schema_v2(entry)
        assert any("requires_serial" in p for p in problems)

    def test_rejects_unknown_resource_scope_kind(self) -> None:
        entry = self._valid_entry()
        entry["resource_scope_kind"] = "bogus"
        problems = validate_tool_schema_v2(entry)
        assert any("bogus" in p for p in problems)

    def test_rejects_resource_scope_key_absent_from_input_schema_properties(
        self,
    ) -> None:
        entry = self._valid_entry()
        entry["resource_scope_keys"] = ["path", "missing_key"]
        problems = validate_tool_schema_v2(entry)
        assert any("missing_key" in p for p in problems)

    def test_accepts_empty_resource_scope_kind_and_keys(self) -> None:
        entry = self._valid_entry()
        entry["resource_scope_kind"] = ""
        entry["resource_scope_keys"] = []
        assert validate_tool_schema_v2(entry) == []
