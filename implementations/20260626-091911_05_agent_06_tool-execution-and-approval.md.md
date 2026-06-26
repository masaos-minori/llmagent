# Implementation: Document partial-completion persistence in tool-execution-and-approval.md

Steps covered: Plan 20260626-091911 — Step 3-1

---

## Goal

Document the canonical partial-completion persistence behavior: when a workflow fails mid-execution, completed steps are recorded via `_handle_partial_completion()` and the task status is set to `"partial"`.

---

## Scope

- **In scope**: `docs/05_agent_06_tool-execution-and-approval.md` — add partial-completion section
- **Out of scope**: runtime code changes

---

## Implementation

### Target file
`docs/05_agent_06_tool-execution-and-approval.md`

### Procedure
1. Read the doc to find the workflow execution lifecycle section.
2. Add "Partial Completion Persistence" section:
   ```
   ## Partial Completion Persistence

   When a workflow fails after some steps have completed, the orchestrator records
   the partial state via `_handle_partial_completion()`:

   - task status is set to `"partial"`
   - completed step names are stored
   - the error type and message are recorded

   This is the canonical write path for partial completion. No ad-hoc inline state
   updates are made in the orchestrator. The session store is the single source of truth.

   Partial completions are visible via `/workflow status` and in the diagnostics store.
   They are NOT automatically resumed — the user must decide how to proceed.
   ```

### Method
Documentation-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "Partial Completion\|partial.*persistence" docs/05_agent_06_tool-execution-and-approval.md` shows the new section.
