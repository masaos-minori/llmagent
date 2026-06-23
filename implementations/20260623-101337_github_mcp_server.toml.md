## Goal

Update the deployed TOML configuration `config/github_mcp_server.toml` so that `allow_force_push` and `require_pr_review` reflect the new safe defaults, keeping the TOML in sync with the Python `GitHubConfig` defaults.

## Scope

**In-Scope:**
- `config/github_mcp_server.toml` lines 22 and 25 — change the two boolean values

**Out-of-Scope:**
- No changes to any Python file
- No new TOML keys

## Assumptions

1. The TOML file contains explicit values that override Python defaults at runtime. Even after Python defaults are changed, the TOML must be updated so the deployed configuration matches the intended policy.
2. The surrounding comments (lines 21, 24) accurately describe the semantics and do not need to change.
3. This is a configuration file change — it takes effect immediately on the next server restart without a code deploy.

## Implementation

### Target file
`config/github_mcp_server.toml`

### Procedure

1. Locate line 22 (`allow_force_push = true`).
2. Change to `allow_force_push = false`.
3. Locate line 25 (`require_pr_review = false`).
4. Change to `require_pr_review = true`.

### Method

Two `Edit` operations.

### Details

**Current (line 22):**
```toml
allow_force_push = true
```

**Replacement:**
```toml
allow_force_push = false
```

**Current (line 25):**
```toml
require_pr_review = false
```

**Replacement:**
```toml
require_pr_review = true
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| TOML parses correctly | `python -c "import tomllib; tomllib.load(open('config/github_mcp_server.toml','rb'))"` | No exception |
| Values correct | `python -c "import tomllib; d=tomllib.load(open('config/github_mcp_server.toml','rb')); assert not d['allow_force_push']; assert d['require_pr_review']"` | No AssertionError |
| GitHubConfig.load() | `python -c "from mcp.github.models_config import GitHubConfig; c=GitHubConfig.load(); assert not c.allow_force_push; assert c.require_pr_review"` | No AssertionError (when run from project root) |
