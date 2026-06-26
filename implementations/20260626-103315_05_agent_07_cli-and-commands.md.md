# Implementation: Update /approve and /reject description in cli-and-commands.md

Steps covered: Plan 20260626-090724 — Phase 4, Step 4-2

---

## Goal

Update `docs/05_agent_07_cli-and-commands.md` to make it explicit that `/approve` and `/reject` resolve **workflow-level approval only** (not per-tool interactive approval), and add a cross-reference to the canonical approval model ADR.

---

## Scope

- **In scope**: `docs/05_agent_07_cli-and-commands.md` — update `/approve` and `/reject` command descriptions
- **Out of scope**: runtime code changes

---

## Assumptions

- The doc already has entries for `/approve` and `/reject`.
- The current description may not distinguish workflow-level from tool-level approval.
- A brief scope note and a cross-reference to `05_agent_06_tool-execution-and-approval.md` is sufficient.

---

## Implementation

### Target file
`docs/05_agent_07_cli-and-commands.md`

### Procedure
1. Read `docs/05_agent_07_cli-and-commands.md` — find the `/approve` and `/reject` entries.
2. Update the `/approve` entry:
   ```
   /approve [reason]
   Approve the pending workflow-level approval gate.
   Resolves the suspended workflow task (execute → verify transition).
   Scope: workflow-level approval only (DB record in workflow_approvals table).
   Does NOT affect per-tool interactive approval prompts.
   See: docs/05_agent_06_tool-execution-and-approval.md — Canonical Approval Model
   ```
3. Update the `/reject` entry similarly:
   ```
   /reject [reason]
   Reject the pending workflow-level approval gate.
   Marks the workflow task as rejected.
   Scope: workflow-level approval only. Does NOT affect per-tool interactive approval.
   See: docs/05_agent_06_tool-execution-and-approval.md — Canonical Approval Model
   ```
4. If a "Approval" section does not exist, add one grouping `/approve` and `/reject` together with a brief intro explaining the two approval layers.

### Method
Documentation edit only. No runtime logic changes.

### Details

Key message to convey:
- Tool-level approval: fires **before** execution, per-tool, via stdin prompt. Resolved by the user typing `y`/`n`.
- Workflow-level approval: fires **after** execute stage, per-task, via `/approve`/`/reject` commands.
- These are independent; `/approve` does not bypass tool-level prompts.

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Confirm: `grep -n "/approve\|/reject\|workflow-level" docs/05_agent_07_cli-and-commands.md` shows updated entries.
- Cross-check: `05_agent_06_tool-execution-and-approval.md` and `05_agent_07_cli-and-commands.md` are mutually consistent.
