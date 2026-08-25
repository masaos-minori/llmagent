# Known Issue: Dirty worktree / detached HEAD not rejected before write operations

## Summary

ADR-012 Decision Details #5 states that `git_checkout`/`git_pull` MUST reject execution against a Dirty Worktree unless a documented safe exception applies, and Detached HEAD MUST be rejected unless explicitly permitted by policy. Current implementation does not check either condition before executing write operations.

## Details

| Field | Value |
|-------|-------|
| ID | GIT-001 |
| Status | Open |
| Severity | High |
| Area | Git MCP server-side write enforcement |
| Related ADR | ADR-012-git-mcp-server-side-write-enforcement |
| Conflicting Source | scripts/mcp_servers/git/git_service.py:129-141 |
| Expected Design | Decision #5: `git_checkout`/`git_pull` MUST reject execution against a Dirty Worktree unless a documented safe exception applies; Detached HEAD MUST be rejected unless explicitly permitted by policy. |
| Observed Implementation | `_run_tool()` validates repo_path and write guard only. No dirty-worktree check (`repo.is_dirty()`) or detached-HEAD check (`repo.head.is_detached`) before write operations. `format_status()` at format_output.py:33 checks dirty state but it is only used for display, not for write-gating. |
| Impact | Users can execute `git_checkout`/`git_pull` on a dirty worktree without warning, potentially losing uncommitted changes. Detached HEAD state is silently accepted, which may cause unexpected behavior when users expect branch-based workflows. |
| Recommended Action | Add `_check_dirty_worktree()` and `_check_detached_head()` methods to `GitSecurityGuards`, called from `_validate_repo()` before write operations. Define safe exceptions (e.g., dry_run mode). |
| Owner | TBD |
| Resolution Target | Next sprint |
