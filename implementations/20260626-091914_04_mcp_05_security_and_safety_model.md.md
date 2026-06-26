# Implementation: Document fail-closed workflow_allowlist policy in security model doc

Steps covered: Plan 20260626-091914 — Step 3-3

---

## Goal

Document the fail-closed `workflow_allowlist` policy in `docs/04_mcp_05_security_and_safety_model.md`, explaining the policy change from fail-open to fail-closed.

---

## Scope

- **In scope**: `docs/04_mcp_05_security_and_safety_model.md` — add cicd workflow_allowlist section
- **Out of scope**: runtime code changes

---

## Implementation

### Target file
`docs/04_mcp_05_security_and_safety_model.md`

### Procedure
1. Find the relevant section (cicd MCP server security or allowlist policy).
2. Add or update:
   ```
   ### cicd MCP: Workflow Allowlist (Fail-Closed)

   The `workflow_allowlist` in `config/cicd_mcp_server.toml` controls which GitHub
   Actions workflow files can be triggered via the cicd MCP server.

   **Policy: fail-closed.**
   - Empty `workflow_allowlist` = deny all workflow triggers (`CicdAuthorizationError`).
   - Non-empty list = only patterns in the list are allowed (glob matching).

   Before this change, an empty list allowed all workflows (fail-open). This was
   a misconfiguration risk: a newly deployed server with no allowlist would allow
   unrestricted workflow triggering.

   **Configuration**:
   ```toml
   # config/cicd_mcp_server.toml
   workflow_allowlist = [
       "my-org/my-repo/.github/workflows/deploy.yml",
       "my-org/my-repo/.github/workflows/ci.yml",
   ]
   ```

   A startup warning is emitted if `workflow_allowlist` is empty.
   ```

### Method
Documentation-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
