"""tests/test_mcp_tool_validators.py
Unit tests for mcp/tool_validators.py and CallToolRequest.validate_args().
"""

from __future__ import annotations

import pytest
from mcp.models import CallToolRequest
from mcp.tool_validators import _VALIDATORS, register_validator, validate_tool_args


class TestRegisterValidator:
    def test_registered_function_is_stored(self) -> None:
        @register_validator("__test_reg__")
        def _v(args: dict) -> None:
            pass

        assert "__test_reg__" in _VALIDATORS

    def test_register_validator_returns_original_function(self) -> None:
        def _v(args: dict) -> None:
            raise ValueError("bad")

        result = register_validator("__test_ret__")(_v)
        assert result is _v


class TestValidateToolArgs:
    def test_no_registered_validator_is_noop(self) -> None:
        validate_tool_args("unknown_tool_xyz", {"anything": 1})  # must not raise

    def test_registered_validator_called(self) -> None:
        @register_validator("__test_called__")
        def _v(args: dict) -> None:
            if not args.get("x"):
                raise ValueError("x required")

        with pytest.raises(ValueError, match="x required"):
            validate_tool_args("__test_called__", {})

    def test_passing_args_does_not_raise(self) -> None:
        @register_validator("__test_pass__")
        def _v(args: dict) -> None:
            if not args.get("x"):
                raise ValueError("x required")

        validate_tool_args("__test_pass__", {"x": "ok"})  # must not raise


class TestCallToolRequestValidateArgs:
    def test_no_validator_registered_is_noop(self) -> None:
        req = CallToolRequest(name="no_validator_tool_xyz", args={"a": 1})
        req.validate_args()  # must not raise

    def test_validator_raises_on_bad_args(self) -> None:
        @register_validator("__test_req_bad__")
        def _v(args: dict) -> None:
            raise ValueError("always bad")

        req = CallToolRequest(name="__test_req_bad__", args={})
        with pytest.raises(ValueError, match="always bad"):
            req.validate_args()


class TestGitCommitValidator:
    def test_blank_message_raises(self) -> None:
        with pytest.raises(ValueError, match="message must not be blank"):
            validate_tool_args("git_commit", {"repo_path": "/repo", "message": "  "})

    def test_relative_repo_path_raises(self) -> None:
        with pytest.raises(ValueError, match="repo_path must be absolute"):
            validate_tool_args(
                "git_commit", {"repo_path": "relative/path", "message": "fix"}
            )

    def test_valid_args_pass(self) -> None:
        validate_tool_args("git_commit", {"repo_path": "/repo", "message": "fix bug"})


class TestGitPushValidator:
    def test_relative_repo_path_raises(self) -> None:
        with pytest.raises(ValueError, match="repo_path must be absolute"):
            validate_tool_args(
                "git_push", {"repo_path": "relative", "remote": "origin"}
            )

    def test_blank_remote_raises(self) -> None:
        with pytest.raises(ValueError, match="remote must not be blank"):
            validate_tool_args("git_push", {"repo_path": "/repo", "remote": ""})

    def test_valid_args_pass(self) -> None:
        validate_tool_args("git_push", {"repo_path": "/repo", "remote": "origin"})


class TestTriggerWorkflowValidator:
    def test_blank_repo_raises(self) -> None:
        with pytest.raises(ValueError, match="repo must not be blank"):
            validate_tool_args(
                "trigger_workflow", {"repo": "", "workflow_id": "ci.yml"}
            )

    def test_blank_workflow_id_raises(self) -> None:
        with pytest.raises(ValueError, match="workflow_id must not be blank"):
            validate_tool_args(
                "trigger_workflow", {"repo": "myorg/myrepo", "workflow_id": ""}
            )

    def test_valid_args_pass(self) -> None:
        validate_tool_args(
            "trigger_workflow", {"repo": "myorg/myrepo", "workflow_id": "ci.yml"}
        )


class TestShellRunValidator:
    def test_blank_string_command_raises(self) -> None:
        with pytest.raises(ValueError, match="command must not be blank"):
            validate_tool_args("shell_run", {"command": "   "})

    def test_empty_list_command_raises(self) -> None:
        with pytest.raises(ValueError, match="command list must not be empty"):
            validate_tool_args("shell_run", {"command": []})

    def test_valid_string_command_passes(self) -> None:
        validate_tool_args("shell_run", {"command": "echo hello"})

    def test_valid_list_command_passes(self) -> None:
        validate_tool_args("shell_run", {"command": ["echo", "hello"]})
