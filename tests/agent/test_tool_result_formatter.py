"""tests/test_tool_result_formatter.py
Unit tests for agent/tool_result_formatter.py — mask_args, build_preview.
"""

from __future__ import annotations

from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_result_formatter import (
    build_github_preview,
    build_preview,
    mask_args,
    turn_limit_hint,
)


def _cfg(**overrides: dict) -> AgentConfig:
    defaults: dict = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "tool_cache_ttl": 300,
        "top_k_search": 20,
        "top_k_rerank": 15,
        "rag_top_k": 5,
        "use_mqe": True,
        "use_search": True,
        "use_rrf": True,
        "use_rerank": True,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "rag_min_score": 0.0,
        "max_chunks_per_doc": 2,
        "use_two_stage_fetch": False,
        "two_stage_max_docs": 2,
        "serial_tool_calls": False,
        "use_semantic_cache": False,
        "semantic_cache_threshold": 0.92,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": [],
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
        "approval_resource_keys": {"path_keys": [], "branch_keys": []},
        "allowed_root": "",
        "mcp_servers": {"_test": {"transport": "http", "url": "http://localhost:8000"}},
    }
    defaults.update(overrides)
    return build_agent_config(defaults)


class TestMaskArgs:
    def test_masks_specified_fields(self) -> None:
        result = mask_args({"password": "secret123", "path": "/tmp/f"}, ["password"])
        assert result == {"password": "***", "path": "/tmp/f"}

    def test_empty_masked_fields_returns_unchanged(self) -> None:
        result = mask_args({"path": "/tmp/f"}, [])
        assert result == {"path": "/tmp/f"}

    def test_empty_args_returns_empty(self) -> None:
        result = mask_args({}, ["secret"])
        assert result == {}

    def test_masked_field_not_in_args_ignored(self) -> None:
        result = mask_args({"path": "/tmp/f"}, ["secret"])
        assert result == {"path": "/tmp/f"}

    def test_all_fields_masked(self) -> None:
        result = mask_args({"a": "1", "b": "2"}, ["a", "b"])
        assert result == {"a": "***", "b": "***"}

    def test_non_string_values_preserved(self) -> None:
        result = mask_args({"path": "/tmp/f", "count": 42, "flag": True}, ["secret"])
        assert result == {"path": "/tmp/f", "count": 42, "flag": True}


class TestBuildPreview:
    def test_write_file_with_path_and_content(self) -> None:
        preview = build_preview(
            "write_file", {"path": "/tmp/a.txt", "content": "hello"}
        )
        assert "/tmp/a.txt" in preview
        assert "hello" in preview

    def test_edit_file_with_file_path_key(self) -> None:
        preview = build_preview(
            "edit_file", {"file_path": "/tmp/b.py", "new_content": "print(1)"}
        )
        assert "/tmp/b.py" in preview
        assert "print(1)" in preview

    def test_delete_file_path_only(self) -> None:
        preview = build_preview("delete_file", {"path": "/tmp/x"})
        assert "/tmp/x" in preview

    def test_delete_directory_with_directory_path(self) -> None:
        preview = build_preview("delete_directory", {"directory_path": "/tmp/dir"})
        assert "/tmp/dir" in preview

    def test_create_directory_with_path(self) -> None:
        preview = build_preview("create_directory", {"path": "/tmp/new"})
        assert "/tmp/new" in preview

    def test_move_file_source_to_destination(self) -> None:
        preview = build_preview("move_file", {"source": "/a", "destination": "/b"})
        assert "/a" in preview
        assert "/b" in preview
        assert "\u2192" in preview

    def test_shell_run_shows_command(self) -> None:
        preview = build_preview("shell_run", {"command": "ls -la"})
        assert "ls -la" in preview

    def test_github_tool_shows_repo(self) -> None:
        preview = build_preview(
            "github_create_issue",
            {"owner": "myorg", "repo": "myrepo", "title": "Bug"},
        )
        assert "myorg/myrepo" in preview

    def test_unknown_tool_falls_back_to_json(self) -> None:
        preview = build_preview("read_text_file", {"path": "/tmp/x"})
        assert "path" in preview
        assert "/tmp/x" in preview

    def test_content_truncated_at_200_chars(self) -> None:
        long_content = "x" * 500
        preview = build_preview(
            "write_file", {"path": "/tmp/f", "content": long_content}
        )
        assert "x" * 500 not in preview

    def test_missing_path_falls_back_to_question_mark(self) -> None:
        preview = build_preview("write_file", {})
        assert "?" in preview

    def test_github_tool_missing_owner_repo(self) -> None:
        preview = build_preview("github_push_files", {})
        assert "?" in preview

    def test_git_checkout_with_repo_and_branch(self) -> None:
        preview = build_preview(
            "git_checkout",
            {"repo_path": "https://github.com/example/repo", "branch": "main"},
        )
        assert "git@" in preview
        assert "https://github.com/example/repo" in preview
        assert "branch=main" in preview
        assert "json" not in preview.lower() or '"repo_path"' not in preview

    def test_git_push_with_repo_and_remote(self) -> None:
        preview = build_preview(
            "git_push",
            {"repo_path": "https://github.com/example/repo", "remote": "origin"},
        )
        assert "git@" in preview
        assert "https://github.com/example/repo" in preview
        assert "remote=origin" in preview

    def test_git_log_with_repo_only(self) -> None:
        preview = build_preview(
            "git_log",
            {"repo_path": "https://github.com/example/repo"},
        )
        assert "git@" in preview
        assert "https://github.com/example/repo" in preview
        assert "branch=" not in preview
        assert "remote=" not in preview

    def test_git_tool_missing_repo_path_shows_placeholder(self) -> None:
        preview = build_preview("git_checkout", {})
        assert "?" in preview


class TestTurnLimitHint:
    def test_turn_limit_hint_multi_line_reports_chars_and_lines(self) -> None:
        hint = turn_limit_hint(omitted_chars=1234, omitted_lines=42, limit=4000)
        assert "1234 chars" in hint
        assert "42 lines" in hint
        assert "4000 chars" in hint

    def test_turn_limit_hint_single_line_reports_one_line(self) -> None:
        hint = turn_limit_hint(omitted_chars=10, omitted_lines=1, limit=100)
        assert "10 chars" in hint
        assert "1 lines" in hint
        assert "100 chars" in hint

    def test_turn_limit_hint_zero_length_edge_case(self) -> None:
        hint = turn_limit_hint(omitted_chars=0, omitted_lines=0, limit=4000)
        assert "0 chars" in hint
        assert "0 lines" in hint
        assert "4000 chars" in hint


class TestBuildGithubPreview:
    def test_owner_and_repo_included(self) -> None:
        preview = build_github_preview(
            {"owner": "myorg", "repo": "myrepo", "branch": "main"}
        )
        assert "myorg/myrepo" in preview

    def test_missing_owner_or_repo_falls_back(self) -> None:
        preview = build_github_preview({"branch": "main"})
        assert "?" in preview

    def test_extra_args_shown_as_json(self) -> None:
        preview = build_github_preview({"owner": "o", "repo": "r", "title": "Fix bug"})
        assert "title" in preview
