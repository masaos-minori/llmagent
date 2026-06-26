# Implementation: Document startup approval restore behavior in cli-and-commands.md

Steps covered: Plan 20260626-091909 — Step 3-1

---

## Goal

Document the startup recovery behavior for pending workflow approvals so users know that pending approvals survive agent restarts and what to expect on next startup.

---

## Scope

- **In scope**: `docs/05_agent_07_cli-and-commands.md` — add startup restore note under `/approve`/`/reject` section
- **Out of scope**: runtime code changes

---

## Assumptions

- The doc already has entries for `/approve` and `/reject` (updated in plan 01, step 4-2).
- Users need to know: if the agent restarts while a workflow is awaiting approval, the state is not lost — it is detected at next startup.

---

## Implementation

### Target file
`docs/05_agent_07_cli-and-commands.md`

### Procedure
1. Read the `/approve`/`/reject` section added in plan 01.
2. Add a "Startup Recovery" note:
   ```
   ### Startup Recovery
   If the agent restarts while a workflow-level approval is pending, the pending state is
   automatically detected at startup from the `workflow_approvals` database table.
   A startup notice is shown: "[startup] Pending workflow approval detected — use /approve or /reject."
   The workflow resumes from the approval gate; no re-execution of prior steps is needed.
   ```

### Method
Documentation-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "Startup Recovery\|approval.*restart" docs/05_agent_07_cli-and-commands.md` shows the new section.
