# Implementation: docs/04_mcp_05_security_and_safety_model.md — fail-open vs fail-closed defaults

## Goal

Add a section to `docs/04_mcp_05_security_and_safety_model.md` that clearly documents which MCP
server settings are fail-open (allow when empty) vs fail-closed (deny when empty), and which are
dangerous when left at defaults.

## Scope

- `docs/04_mcp_05_security_and_safety_model.md` only.
- No code changes.

## Assumptions

1. The doc already exists and covers auth_token, allowlists, and denylist behavior at a high level.
2. The new section is additive; existing content is not modified.

## Implementation

### Target file

`docs/04_mcp_05_security_and_safety_model.md`

### Procedure

Append (or insert in a logical location) a new section:

```markdown
## Fail-open vs Fail-closed Defaults

"Fail-closed" means the setting denies access when the list is empty.
"Fail-open" means the setting allows all access when the list is empty.

| Server | Setting | Default | Behavior when empty |
|---|---|---|---|
| shell-mcp | `command_allowlist` | `[]` | **Fail-closed** — all shell commands denied |
| sqlite-mcp | `db_allowlist` | `[]` | **Fail-closed** — all DB queries denied |
| git-mcp | `allowed_repo_paths` | `[]` | **Fail-closed** — all repo access denied |
| github-mcp | `allowed_repos` | `[]` | **Fail-closed** — all GitHub write ops denied |
| cicd-mcp | `workflow_allowlist` | `[]` | **Fail-open** — all workflows can be triggered |
| github-mcp | `allowed_workflows` | `[]` | **Fail-open** — all workflows allowed |

### Dangerous defaults to review before production deployment

- `shell-mcp`: `sandbox_backend = "none"` (default) means no OS-level sandboxing.
  Set to `"firejail"` for production; visible in `/health` response.
- `cicd-mcp`: `workflow_allowlist = []` is fail-open; explicitly list permitted workflows.
- `github-mcp`: `allow_force_push = true` (default); set to `false` in production.

### Startup audit

`audit_security_defaults()` in `agent/repl_health.py` runs at startup and logs:
- All fail-closed settings that are empty (informational — access is correctly denied)
- All fail-open settings that are empty (warning — unintended access may be allowed)
- A summary line: `Security posture summary — fail-closed (...): ...; fail-open (...): ...`
```

### Method

Read the existing file first, then append the new section after the last existing section.

### Details

Keep the table rows aligned with pipe characters for readability in rendered Markdown.

## Validation plan

| Check | Action | Target |
|---|---|---|
| File exists | Read the file | No error |
| Section added | Grep for "Fail-open vs Fail-closed" | Found |
| No broken links | Manual review | All cross-references valid |
