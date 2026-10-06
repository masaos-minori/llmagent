# Configure DENY-ALL allowlists for git, github, and cicd MCP servers

## Summary

git, github, and cicd MCP servers reject all operations due to empty allowlists. This causes DENY-ALL warnings and prevents all repository operations.

## Background

Three MCP servers use a fail-closed security model: when their allowlist is empty, they deny all operations. The current configuration has empty allowlists for all three servers.

## Problem

AgentREPL startup produces three DENY-ALL warnings and two cicd-mcp service-level warnings:
```
DENY-ALL detected: git.allowed_repo_paths is empty. git-mcp will reject ALL repository operations.
DENY-ALL detected: github.allowed_repos is empty. github-mcp will reject ALL repo access requests.
DENY-ALL detected: cicd.workflow_allowlist is empty. cicd-mcp will reject ALL workflow trigger requests.
cicd-mcp: repo_allowlist is empty — all repository operations will be denied
cicd-mcp: workflow_allowlist is empty — all workflow triggers will be denied
```

## Reason for Change

Empty allowlists cause complete denial of service for git/GitHub/workflow operations. These are critical for the agent's ability to perform repository operations.

## Implementation Intent

Configure the allowlists for each MCP server with the appropriate values. Each server needs its own allowlist populated based on the required repositories and workflows.

## Target Files or Areas

- `/opt/llm/config/git_mcp_server.toml` — allowed_repo_paths
- `/opt/llm/config/github_mcp_server.toml` — allowed_repos
- `/opt/llm/config/cicd_mcp_server.toml` — repo_allowlist, workflow_allowlist

## Required Changes

### git_mcp_server.toml
Set `allowed_repo_paths` to include required repository paths:
```toml
allowed_repo_paths = ["/home/sugimoto/llmagent", "/opt/llm"]
```

### github_mcp_server.toml
Set `allowed_repos` to include required repositories:
```toml
allowed_repos = ["masaos-minori/llmagent"]
```

### cicd_mcp_server.toml
Set `repo_allowlist` and `workflow_allowlist` to include required repositories and workflows:
```toml
repo_allowlist = [
  "masaos-minori/llmagent",
]

workflow_allowlist = [
  "masaos-minori/llmagent/.github/workflows/ci.yml",
  "masaos-minori/llmagent/.github/workflows/deploy.yml",
]
```

## Constraints

- Do not use wildcard patterns — list explicit paths/repos
- Preserve existing settings (read_only, protected_branches, etc.)
- Do not add unnecessary entries

## Out of Scope

- Adding new MCP servers
- Changing the fail-closed security model
- Modifying the DENY-ALL detection logic

## Dependencies

- N/A: none

## Acceptance Criteria

- [ ] No DENY-ALL warnings for git, github, or cicd MCP servers
- [ ] Repository operations succeed for configured repos
- [ ] Workflow triggers succeed for configured workflows

## Testing Expectations

- Run `bash /opt/llm/start_agent.sh` and verify no DENY-ALL warnings
- Test git operations (e.g., `git_status`) to confirm they work

## Documentation Impact

Update deployment documentation to document required allowlist configuration.

## Unresolved Questions

- What is the correct `allowed_repo_paths` value? (currently assumed: `/home/sugimoto/llmagent`, `/opt/llm`)
- What is the correct `allowed_repos` value? (currently assumed: `masaos-minori/llmagent`)
- What specific workflow files should be in the cicd `workflow_allowlist`?

## Evidence

- Startup output: 3 DENY-ALL warnings + 2 cicd-mcp service-level warnings
- Source: `/opt/llm/config/git_mcp_server.toml` (allowed_repo_paths = [])
- Source: `/opt/llm/config/github_mcp_server.toml` (allowed_repos = [])
- Source: `/opt/llm/config/cicd_mcp_server.toml` (repo_allowlist = [], workflow_allowlist = [])
- Source: `scripts/agent/services/security_audit.py:166,177,190` (DENY-ALL detection)
- Source: `scripts/mcp_servers/cicd/cicd_service_guards.py:35-37` (cicd-mcp service-level warnings)

## Priority

High
