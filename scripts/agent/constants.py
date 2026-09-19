#!/usr/bin/env python3
"""scripts/agent/constants.py

Default constant tables for configuration builders and dataclasses.

This module is a leaf module — no other module imports from it except
config_dataclasses.py. It provides the canonical source of truth for
the six _DEFAULT_* tables, eliminating the two-sources-of-truth problem
where these values were duplicated between config_builders.py and
config_dataclasses.py.

Import from here:  from agent.constants import _DEFAULT_...
"""


_DEFAULT_PLAN_BLOCKED_TOOLS: list[str] = [
    "write_file",
    "create_directory",
    "delete_file",
    "delete_directory",
]
_DEFAULT_APPROVAL_RISK_RULES: dict[str, str] = {
    "write_file": "medium",
    "edit_file": "medium",
    "create_directory": "medium",
    "move_file": "medium",
    "delete_file": "high",
    "delete_directory": "high",
    "shell_run": "high",
    "github_push_files": "high",
    "github_create_or_update_file": "high",
    "github_delete_file": "high",
    "github_merge_pull_request": "high",
    "github_create_branch": "medium",
    "github_create_pull_request": "medium",
    "github_update_pull_request": "medium",
    "github_create_issue": "medium",
    "github_add_issue_comment": "medium",
}
_DEFAULT_PROTECTED_PATHS: list[str] = [
    "/opt/",
    "/etc/",
    "/boot/",
    "/usr/",
    "/bin/",
    "/sbin/",
]
_DEFAULT_SHELL_SAFE_PREFIXES: list[str] = [
    "ls",
    "cat",
    "echo",
    "git log",
    "git status",
    "git diff",
    "git show",
    "git branch",
    "pwd",
    "find",
    "grep",
]
_DEFAULT_RESOURCE_KEYS: dict[str, list[str]] = {
    "path_keys": ["path", "file_path", "directory_path", "source", "destination"],
    "branch_keys": ["branch", "base", "head"],
}
_DEFAULT_DRY_RUN_TOOLS: list[str] = [
    "write_file",
    "edit_file",
    "create_directory",
    "delete_file",
    "delete_directory",
    "move_file",
]
