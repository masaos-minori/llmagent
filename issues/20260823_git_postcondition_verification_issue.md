# Known Issue: Postcondition verification missing after git write operations

## Summary

ADR-012 Decision Details #6 states that postcondition verification MUST confirm the resulting branch/HEAD and detect unresolved conflicts before reporting success. Current implementation reports success immediately after the git operation completes without verifying the expected outcome.

## Details

| Field | Value |
|-------|-------|
| ID | GIT-002 |
| Status | Open |
| Severity | Medium |
| Area | Git MCP server-side write enforcement |
| Related ADR | ADR-012-git-mcp-server-side-write-enforcement |
| Conflicting Source | scripts/mcp_servers/git/format_output.py:118-156 |
| Expected Design | Decision #6: Postcondition verification MUST confirm the resulting branch/HEAD and detect unresolved conflicts before reporting success. A `git` command that exits non-zero already fails today, but a low-level "did we actually end up where we intended" check is not the same guarantee. |
| Observed Implementation | Write operations (`format_checkout`, `format_pull`, `format_push`) return success immediately after the GitPython call completes. No verification that the resulting branch/HEAD matches the requested branch, no conflict detection after pull/merge, no verification that push succeeded with the expected remote state. |
| Impact | Silent failures: a checkout may appear successful but leave the working tree in an inconsistent state; a pull may merge unexpectedly without detecting conflicts; a push may fail silently if the remote rejects the update. |
| Recommended Action | Add postcondition verification after each write operation: verify branch name after checkout, verify merge result after pull, verify push status after push. Report specific failure messages instead of generic success. |
| Owner | TBD |
| Resolution Target | Next sprint |
