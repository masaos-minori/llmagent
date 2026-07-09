# Implementation: docs — GitHub MCP deny controls documentation

## Goal

Add explicit production examples for GitHub MCP deny controls in `04_mcp_05_security_and_safety_model.md`.

## Scope

- `docs/04_mcp_05_security_and_safety_model.md`

## Assumptions

1. `path_denylist`, `protected_branches`, `allow_force_push`, `require_pr_review` are already documented at a basic level.
2. No runtime behavior changes are required.

## Implementation

### Target file

`docs/04_mcp_05_security_and_safety_model.md`

### Procedure

1. Add production examples for:
   - `path_denylist`: protect `.github/**` and deployment paths
   - `protected_branches`: protect `main`, `master`, `release/*`
   - `allow_force_push`: describe risks and recommendation (disabled in production)
   - `require_pr_review`: guidance on PR review requirements
2. Use concrete TOML config snippets for each control.

### Details

- Format examples as code blocks with realistic values.
- Cross-reference to `04_mcp_06_configuration_and_operations.md` for full config reference.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| GitHub controls documented | `rg "path_denylist\|protected_branches" docs/04_mcp_05_security_and_safety_model.md` | Matches for both |
