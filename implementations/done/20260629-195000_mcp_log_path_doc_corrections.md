# Implementation Design: MCP Server Log Path Documentation Corrections

## Goal

Update `docs/04_mcp_06_configuration_and_operations.md` with verified application log paths and audit log paths for all 11 MCP servers, correcting three confirmed inaccuracies in the existing tables.

## Scope

- **In-Scope**:
  - Correct the per-server application log table: update sqlite-mcp row
  - Correct the per-server audit log table: fix github-mcp filename, correct git-mcp and sqlite-mcp descriptions
  - Update the inline note about cicd-mcp, git-mcp, and sqlite-mcp audit logging
  - Fix stale "no server module exists yet" comment for sqlite-mcp health check section
- **Out-of-Scope**:
  - Changing log format or log rotation
  - Adding FileHandler to cicd-mcp, git-mcp, or sqlite-mcp server code
  - Implementing git-mcp or sqlite-mcp audit logging
  - Modifying deploy scripts

## Affected Files

1. `docs/04_mcp_06_configuration_and_operations.md` — primary target
   - Line ~264: `github-audit.log` → `github_audit.log`
   - Line ~133: sqlite-mcp health check comment update
   - Line ~276: Add sqlite-mcp to audit log note
   - Line ~292: sqlite-mcp app log row — "No server module yet" → "No dedicated log file"
   - Line ~302: github-mcp audit log — `github-audit.log` → `github_audit.log`
   - Line ~307: git-mcp audit log — update description
   - Line ~308: sqlite-mcp audit log — update description

## Verification Commands

```bash
grep -n "github-audit.log" docs/04_mcp_06_configuration_and_operations.md  # should return no results
grep -n "No server module" docs/04_mcp_06_configuration_and_operations.md   # should return no results
grep -n "sqlite-mcp" docs/04_mcp_06_configuration_and_operations.md         # should show updated rows only
```

## Acceptance Criteria

- [x] No remaining `github-audit.log` references in docs
- [x] No remaining "No server module" text in docs
- [x] sqlite-mcp rows correctly describe SELECT-only implementation
- [x] git-mcp audit log row clarifies config key exists but no write code
- [x] sqlite-mcp audit log row clarifies config key is not parsed
