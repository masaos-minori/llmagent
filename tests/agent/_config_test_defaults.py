"""tests/agent/_config_test_defaults.py

Shared overrides for tests that call build_agent_config()/ProductionConfigValidator
against a minimal config dict. ProductionConfigValidator unconditionally requires
tool_definitions_strict/routing_drift_strict, and a non-empty allowed_tools
(scripts/shared/production_config_validator.py), so any minimal test config dict
must merge this in unless the test specifically exercises the missing-flags error
path (see tests/agent/test_config_builders.py's _MIN_CFG, which intentionally
omits these).
"""

from shared.tool_registry import get_registry

STRICT_PRODUCTION_OVERRIDES: dict[str, bool] = {
    "tool_definitions_strict": True,
    "routing_drift_strict": True,
}

# Mirrors config/agent.toml's [approval_risk_rules] table. ProductionConfigValidator
# requires git_checkout/git_pull/git_push to resolve to an effective risk of
# HIGH, and several tests assert on the medium/high risk classification of
# other tools (e.g. write_file). A test config dict that sets its own
# "approval_risk_rules" replaces this at the top level (the override is not
# deep-merged), so any such override must spread this in alongside its
# test-specific rule(s).
# The floor subset alone, for a test that wants to exercise an otherwise-empty
# approval_risk_rules (e.g. to verify tier-based fallback classification for
# some other tool) while still satisfying the git risk-floor requirement above.
GIT_RISK_FLOOR: dict[str, str] = {
    "git_checkout": "high",
    "git_pull": "high",
    "git_push": "high",
}

ALL_APPROVAL_RISK_RULES: dict[str, str] = {
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
    "git_checkout": "high",
    "git_pull": "high",
    "git_push": "high",
}

# Every registered tool name, so tests that don't care about allowlist
# restriction aren't accidentally denied a tool call by an empty-list default
# now that ProductionConfigValidator rejects allowed_tools=[].
ALL_TOOL_NAMES: list[str] = sorted(get_registry().get_all_tool_names())

# A tier for every registered tool, mirroring config/agent.toml's
# [tool_safety_tiers] section. ProductionConfigValidator now requires every
# registered tool to appear here, so a test config listing only a subset of
# tools is no longer valid even if it never exercises the rest.
ALL_TOOL_SAFETY_TIERS: dict[str, str] = {
    "read_text_file": "READ_ONLY",
    "list_directory": "READ_ONLY",
    "directory_tree": "READ_ONLY",
    "search_files": "READ_ONLY",
    "grep_files": "READ_ONLY",
    "write_file": "WRITE_SAFE",
    "edit_file": "WRITE_SAFE",
    "create_directory": "WRITE_SAFE",
    "move_file": "WRITE_SAFE",
    "delete_file": "WRITE_DANGEROUS",
    "delete_directory": "WRITE_DANGEROUS",
    "shell_run": "ADMIN",
    "search_web": "READ_ONLY",
    "browser_fetch": "READ_ONLY",
    "github_search_repositories": "READ_ONLY",
    "github_search_code": "READ_ONLY",
    "github_get_file_contents": "READ_ONLY",
    "github_list_issues": "READ_ONLY",
    "github_list_branches": "READ_ONLY",
    "github_create_branch": "WRITE_SAFE",
    "github_create_issue": "WRITE_SAFE",
    "github_add_issue_comment": "WRITE_SAFE",
    "github_push_files": "WRITE_DANGEROUS",
    "github_create_or_update_file": "WRITE_DANGEROUS",
    "github_delete_file": "WRITE_DANGEROUS",
    "github_create_pull_request": "WRITE_DANGEROUS",
    "github_update_pull_request": "WRITE_DANGEROUS",
    "github_merge_pull_request": "WRITE_DANGEROUS",
    "search_docs": "READ_ONLY",
    "get_chunk": "READ_ONLY",
    "outline": "READ_ONLY",
    "stats": "READ_ONLY",
    "grep_docs": "READ_ONLY",
    "index_paths": "WRITE_SAFE",
    "refresh_index": "WRITE_SAFE",
    "rag_run_pipeline": "READ_ONLY",
    "rag_debug_pipeline": "READ_ONLY",
    "get_file_info": "READ_ONLY",
    "github_get_commit": "READ_ONLY",
    "github_get_issue": "READ_ONLY",
    "github_get_pull_request": "READ_ONLY",
    "github_list_commits": "READ_ONLY",
    "github_list_pull_requests": "READ_ONLY",
    "github_search_issues": "READ_ONLY",
    "github_search_pull_requests": "READ_ONLY",
    "list_directory_with_sizes": "READ_ONLY",
    "read_media_file": "READ_ONLY",
    "read_multiple_files": "READ_ONLY",
    "rag_list_documents": "READ_ONLY",
    "rag_delete_document": "WRITE_DANGEROUS",
    "get_workflow_runs": "READ_ONLY",
    "get_workflow_status": "READ_ONLY",
    "get_workflow_logs": "READ_ONLY",
    "trigger_workflow": "WRITE_DANGEROUS",
    "git_status": "READ_ONLY",
    "git_log": "READ_ONLY",
    "git_diff": "READ_ONLY",
    "git_branch": "READ_ONLY",
    "git_show": "READ_ONLY",
    "git_add": "WRITE_SAFE",
    "git_commit": "WRITE_SAFE",
    "git_checkout": "WRITE_DANGEROUS",
    "git_pull": "WRITE_DANGEROUS",
    "git_push": "WRITE_DANGEROUS",
}
