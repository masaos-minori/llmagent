#!/usr/bin/env python3
"""scripts/agent/constants.py — Default constant tables for configuration builders and dataclasses.

This module is a leaf module: no other module imports from it except
config_dataclasses.py. It provides the canonical source of truth for
the three _DEFAULT_* tables, eliminating the two-sources-of-truth problem
where these values were duplicated between config_builders.py and
config_dataclasses.py.

agentcfg003 (REQ-011): the per-tool default tables (_DEFAULT_APPROVAL_RISK_RULES,
_DEFAULT_RESOURCE_KEYS, _DEFAULT_DRY_RUN_TOOLS) are removed: the removed config
maps have no compatibility reader, and each concept's single source is the
producers' declared tool metadata (shared.tool_metadata / shared.tool_registry).

Import from here:  from agent.constants import _DEFAULT_...
"""

_DEFAULT_PLAN_BLOCKED_TOOLS: list[str] = [
    "write_file",
    "create_directory",
    "delete_file",
    "delete_directory",
]
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
