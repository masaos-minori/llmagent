# Implementation: Update github_mcp_server.toml for allowed_workflows change

Steps covered: Plan 20260626-091915 — Step 2A-1

---

## Goal

Update `config/github_mcp_server.toml` to reflect the `allowed_workflows` policy change: remove the field if the feature was removed, or add a fail-closed default comment if it was made fail-closed.

---

## Scope

- **In scope**: `config/github_mcp_server.toml` — `allowed_workflows` field
- **Out of scope**: service_security.py (step 1-1); docs (steps 2A-2, 3-1)

---

## Assumptions

- `config/github_mcp_server.toml` currently has an `allowed_workflows = []` or similar field.
- If the feature was removed (step 1-1 outcome): remove the field.
- If the feature was made fail-closed: add a comment explaining the semantics.

---

## Implementation

### Target file
`config/github_mcp_server.toml`

### Procedure
1. Read `config/github_mcp_server.toml`.
2. If `allowed_workflows` feature was removed:
   - Delete the `allowed_workflows` field entirely.
   - Add a comment: `# allowed_workflows removed — unimplemented feature, see plan 20260626-091915`.
3. If `allowed_workflows` was made fail-closed:
   - Update the comment:
     ```toml
     # Fail-closed: empty list denies all workflow triggers.
     # Add allowed workflow patterns (glob) to enable triggering.
     # allowed_workflows = []  # uncomment and populate to allow specific workflows
     ```

### Method
Config-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — toml lint must pass.
- Confirm: server starts correctly with the updated config.
