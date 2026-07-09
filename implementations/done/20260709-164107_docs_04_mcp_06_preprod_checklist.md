# Implementation: docs/04_mcp_06_configuration_and_operations.md — Add fail-closed checklist item

## Goal

Add a Pre-Production checklist item requiring `allowed_repos_mode="fail_closed"` in `github_mcp_server.toml`.

## Scope

- `docs/04_mcp_06_configuration_and_operations.md` only.
- One checklist item in the "Pre-Production Fail-Open Checklist" section (around line 839).

## Assumptions

1. The section and line numbers match the actual file content.

## Implementation

### Target file

`docs/04_mcp_06_configuration_and_operations.md`

### Procedure

Add a new checklist item after the existing `allowed_repos` line in the Pre-Production Fail-Open Checklist:

```markdown
- [ ] `allowed_repos_mode = "fail_closed"` in `github_mcp_server.toml` (`"fail_open"` is rejected at production startup)
```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Manual review | `git diff docs/04_mcp_06_configuration_and_operations.md` | checklist item added correctly |
