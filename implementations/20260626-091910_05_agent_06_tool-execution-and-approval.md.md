# Implementation: Document removal of direct-execution fallback in tool-execution-and-approval.md

Steps covered: Plan 20260626-091910 — Step 3-1

---

## Goal

Update `docs/05_agent_06_tool-execution-and-approval.md` to document that the direct-execution fallback has been removed and the orchestrator now fails-closed when workflow creation fails.

---

## Scope

- **In scope**: `docs/05_agent_06_tool-execution-and-approval.md` — add "Fail-Closed Policy" section
- **Out of scope**: runtime code changes

---

## Assumptions

- The doc exists and covers workflow execution paths.
- The new section should explain: (a) what the old fallback was, (b) why it was removed, (c) what happens now when workflow creation fails.

---

## Implementation

### Target file
`docs/05_agent_06_tool-execution-and-approval.md`

### Procedure
1. Read the doc to find the right location (after workflow execution path description).
2. Add "Fail-Closed Execution Policy" section:
   ```
   ## Fail-Closed Execution Policy

   The orchestrator does NOT fall back to direct (unapproved) execution when a workflow
   cannot be created. If workflow creation fails, a `WorkflowCreationError` is raised and
   the task is rejected with a clear error message.

   **Before (removed)**: orchestrator would execute tool calls directly, bypassing
   workflow-level approval checks, when no workflow plan was available.

   **After**: `WorkflowCreationError` is raised. The user must fix the underlying cause
   (missing plan, invalid config) and retry.

   This is a fail-closed policy: safety is preferred over availability.
   ```

### Method
Documentation-only change.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "Fail-Closed\|WorkflowCreationError" docs/05_agent_06_tool-execution-and-approval.md` shows the new section.
