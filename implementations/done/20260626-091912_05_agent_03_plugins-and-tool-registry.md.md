# Implementation: Document strict plugin tool contract validation in plugins-and-tool-registry.md

Steps covered: Plan 20260626-091912 — Step 3-1

---

## Goal

Document that `register_tool()` now enforces a strict tool contract and raises `ValueError` on violations, replacing the previous warning-only behavior.

---

## Scope

- **In scope**: `docs/05_agent_03_plugins-and-tool-registry.md` (or equivalent plugin registry doc) — add "Tool Contract" section
- **Out of scope**: runtime code changes

---

## Implementation

### Target file
`docs/05_agent_03_plugins-and-tool-registry.md`

### Procedure
1. Find the plugin registration doc (may be `05_agent_03_*` or `04_mcp_*`).
2. Add "Tool Contract Enforcement" section:
   ```
   ## Tool Contract Enforcement

   `register_tool()` enforces the following contract. Violations raise `ValueError` at
   registration time (not at call time):

   - `name`: required, non-empty string, unique in this registry
   - `description`: required, non-empty string
   - `inputSchema`: required, must be a JSON Schema object (`{"type": "object", ...}`)

   Tool conflicts (duplicate name) are detected via `_validate_tool_conflicts()` and
   also raise `ValueError` (`strict_mode=True` is the only supported mode).

   **Why raise instead of warn?**
   Silent warnings were missed in production, causing unexpected behavior at call time.
   Fail-fast at registration makes the error unmissable.
   ```

### Method
Documentation-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "Tool Contract\|register_tool.*raises" docs/05_agent_03_plugins-and-tool-registry.md` shows the section.
