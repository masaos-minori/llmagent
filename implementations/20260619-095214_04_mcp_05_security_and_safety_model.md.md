# Implementation: Document Deny-All Behavior and Intentional Lockdown Procedure

## Goal

Add a section to `docs/04_mcp_05_security_and_safety_model.md` that:
- Explains what deny-all means for each fail-closed allowlist
- Documents how to intentionally configure a lockdown and suppress startup warnings
- Explains how to verify deny-all state at runtime

## Scope

- `docs/04_mcp_05_security_and_safety_model.md` — new `## Intentional deny-all lockdown` section

Out of scope:
- Code changes
- Enforcement logic changes

## Assumptions

1. The doc already has a table showing which settings are fail-closed (lines 19-23 confirmed). The new section extends this with operational procedure.
2. After Steps 1-2 are implemented, `security_lockdown_enabled` is a real config option.
3. The audience is an operator who is intentionally locking down the agent for a restricted deployment.

## Implementation

### Target file

`docs/04_mcp_05_security_and_safety_model.md`

### Procedure

1. Locate the fail-closed table (around lines 19-23).
2. After the table, or at the end of the file, add a new `## Intentional deny-all lockdown` section.

### Method

New prose section with a procedure list, a config example, and verification commands.

### Details

**Subsection content outline:**

```
## Intentional deny-all lockdown

An empty fail-closed allowlist disables an entire MCP server's operation category.
This is the correct behavior for security-restricted deployments that want to prevent
certain tool categories entirely (e.g., no shell commands, no DB queries).

### Which settings cause deny-all

| Setting | Server | Effect when empty |
|---------|--------|-------------------|
| `shell.command_allowlist` | shell-mcp | All shell commands denied |
| `sqlite.db_allowlist` | sqlite-mcp | All DB queries denied |
| `git.allowed_repo_paths` | git-mcp | All git operations denied |
| `github.allowed_repos` | github-mcp | All repo access denied |

### Configuring an intentional lockdown

1. Set the desired allowlist(s) to empty in the relevant TOML:
   ```toml
   # shell_mcp_server.toml
   command_allowlist = []   # deny all shell commands
   ```

2. Acknowledge the lockdown in `agent.toml` or `common.toml` to suppress
   startup warnings:
   ```toml
   security_lockdown_enabled = true
   ```

3. Restart the agent. The startup log will show:
   ```
   INFO Security: security_lockdown_enabled=True — deny-all warnings suppressed
   ```

### Verifying deny-all state at runtime

At startup, `audit_security_defaults()` logs each deny-all state:
```
WARNING DENY-ALL detected: shell.command_allowlist is empty. shell-mcp will
        reject ALL shell commands. Verify this is intentional or add allowed
        commands to shell_mcp_server.toml.
```

If `security_lockdown_enabled=False` (default), these warnings appear at every
startup — a deliberate reminder to review the config. Set it to `true` only
when the deny-all state is confirmed intentional.

### Reverting a lockdown

Add the allowed values back to the relevant TOML and set
`security_lockdown_enabled = false`. Restart the agent to apply.
```

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Pre-commit | `pre-commit run --all-files` | pass |
| Manual review | Read the new section | lockdown procedure is clear; warnings/suppression is explained |
| Accuracy | Verify `security_lockdown_enabled` key matches config_dataclasses.py field | confirmed |
| Accuracy | Verify deny-all table matches the fail-closed table already in the doc | no contradictions |
