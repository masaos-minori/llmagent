# Implementation: Add canonical fail-open/closed policy table to MCP security docs

Steps covered: Plan 20260626-091919 — All steps (3 docs, docs-only)

---

## Goal

Add a canonical fail-open/closed policy reference table to MCP docs covering all MCP servers and their security controls.

---

## Scope

- **In scope**:
  - `docs/04_mcp_05_security_and_safety_model.md`: canonical policy table
  - `docs/04_mcp_04_server_catalog.md`: per-server security summary column
  - `docs/04_mcp_06_configuration_and_operations.md`: cross-reference to policy table
- **Out of scope**: runtime code changes

---

## Implementation

### Target files
- `docs/04_mcp_05_security_and_safety_model.md`
- `docs/04_mcp_04_server_catalog.md`
- `docs/04_mcp_06_configuration_and_operations.md`

### Procedure

**04_mcp_05 (primary location for policy table)**:
Add:
```
## Fail-Open / Fail-Closed Policy Reference

| Server | Control | Default | Policy | Notes |
|--------|---------|---------|--------|-------|
| cicd MCP | workflow_allowlist | `[]` | **Fail-closed** | Empty list denies all |
| shell MCP | sandbox_backend | `"firejail"` | **Fail-closed** | Missing binary → startup error |
| github MCP | allowed_workflows | (removed or `[]`) | **Fail-closed** | See plan 20260626-091915 |
| github MCP | repo_allowlist | `[]` | **Fail-closed** | Empty list denies all repo access |

Legend:
- Fail-closed: missing/empty config denies access (safe default)
- Fail-open: missing/empty config allows access (unsafe, avoid in production)
```

**04_mcp_04 (per-server catalog)**:
Add a "Fail-Closed?" column to the server table, filled from the policy table above.

**04_mcp_06 (cross-reference)**:
Add: "See `04_mcp_05_security_and_safety_model.md` for the full fail-open/closed policy table."

### Method
Documentation-only change. The policy table consolidates decisions made in plans 07-11.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "Fail-Open\|Fail-Closed\|policy.*table" docs/04_mcp_05_security_and_safety_model.md` shows the table.
