# Implementation: docs — Clarify auth_token="" local/development behavior

## Goal

Add explicit local/development compatibility framing and production prohibition for `auth_token=""` to both security docs.

## Scope

- `docs/04_mcp_05_security_and_safety_model.md`: expand Authentication section
- `docs/04_mcp_06_configuration_and_operations.md`: add cross-referencing note

No code changes.

## Implementation

### Target files

1. `docs/04_mcp_05_security_and_safety_model.md`
2. `docs/04_mcp_06_configuration_and_operations.md`

### Procedure

See plan design section for exact text to add.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Local/dev framing present | `grep -n "local/development compatibility" docs/04_mcp_05_security_and_safety_model.md` | ≥ 1 match |
| Production prohibition stated | `grep -n "must not be used in production" docs/04_mcp_05_security_and_safety_model.md` | ≥ 1 match |
| No code changed | `git diff --stat -- scripts/` | empty |
