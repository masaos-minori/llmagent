# Implementation: docs/04_mcp_05_security_and_safety_model.md — Prohibit fail_open in production

## Goal

Add one sentence to the security model documentation stating that `allowed_repos_mode="fail_open"` is prohibited in production mode.

## Scope

- `docs/04_mcp_05_security_and_safety_model.md` only.
- One sentence after the existing mode table (after line 64).

## Assumptions

1. The line numbers and section structure match the actual file.

## Implementation

### Target file

`docs/04_mcp_05_security_and_safety_model.md`

### Procedure

Insert the following sentence after the existing mode table (after line 64):

```markdown
`allowed_repos_mode="fail_open"` is prohibited in production
(`security_profile="production"`) — startup raises `RuntimeError`. It
remains available in local/development mode for backward compatibility
(startup emits a warning instead).
```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Manual review | `git diff docs/04_mcp_05_security_and_safety_model.md` | sentence added correctly |
