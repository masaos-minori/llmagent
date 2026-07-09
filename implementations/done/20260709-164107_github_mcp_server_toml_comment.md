# Implementation: config/github_mcp_server.toml — Replace misleading comment

## Goal

Replace the misleading `"backward compat default"` wording in the `allowed_repos_mode` comment with accurate description.

## Scope

- `config/github_mcp_server.toml` lines 14-16 only.
- Comment-only change; no functional effect.

## Assumptions

1. The file path and line range match the actual file content.

## Implementation

### Target file

`config/github_mcp_server.toml`

### Procedure

Replace lines 14-16's comment block.

### Details

Before:

```toml
# allowed_repos_mode: behaviour when allowed_repos is empty
# "fail_open" = allow all (backward compat default); "fail_closed" = deny all (recommended for production)
allowed_repos_mode = "fail_closed"
```

After:

```toml
# allowed_repos_mode: behaviour when allowed_repos is empty
# "fail_open" = allow all when allowed_repos is empty; retained for backward compatibility.
# "fail_closed" = deny all when allowed_repos is empty; default and recommended.
allowed_repos_mode = "fail_closed"
```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Manual review | `git diff config/github_mcp_server.toml` | comment updated correctly |
