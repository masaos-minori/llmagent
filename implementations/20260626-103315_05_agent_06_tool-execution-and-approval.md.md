# Implementation: Add canonical approval model ADR and architecture diagram

Steps covered: Plan 20260626-090724 — Phase 1 Step 1-3, Phase 4 Step 4-1

---

## Goal

Add an Architecture Decision Record (ADR) and a canonical model boundary diagram to `docs/05_agent_06_tool-execution-and-approval.md` that clearly defines the two approval layers, their boundaries, and their coexistence rules.

---

## Scope

- **In scope**: edit `docs/05_agent_06_tool-execution-and-approval.md` — add ADR section and boundary diagram
- **Out of scope**: runtime code changes

---

## Assumptions

- The doc file exists and covers tool execution and approval flows.
- The canonical approval model is: **both layers coexist; they have different granularity and are not mutually exclusive**.
- Tool-level approval = per-tool, ephemeral, stdin-interactive.
- Workflow-level approval = per-task, DB-persisted, `/approve`/`/reject` CLI.

---

## Implementation

### Target file
`docs/05_agent_06_tool-execution-and-approval.md`

### Procedure
1. Read the existing file to find the best insertion point (likely after the existing approval flow description).
2. Add a new section `## Canonical Approval Model (ADR-001)` with:
   - Decision date: 2026-06-26
   - Status: Accepted
   - Context: two approval layers exist; they must coexist without conflict
   - Decision: both layers are canonical; "canonical" means boundaries and responsibilities are explicit, not exclusive
   - Boundary table (see Details)
   - Coexistence rules (see Details)
3. Add a text-based architecture diagram (ASCII or markdown table) showing the flow:
   ```
   User prompt
     └─► Orchestrator
           └─► WorkflowEngine (plan → execute → [approval gate] → verify)
                 └─► repository_gateway.py (tool-call batch)
                       └─► run_approval_checks (per-tool, MEDIUM/HIGH risk)
                             └─► stdin prompt → approved/denied
                 └─► _gate_approval() [when require_approval=True]
                       └─► WorkflowPendingApprovalError
                             └─► /approve or /reject command
   ```

### Method
Document edit only. No code changes.

### Details

**Boundary table to add:**

| Axis | Tool-level Approval | Workflow-level Approval |
|------|---------------------|------------------------|
| Implementation | `agent/tool_approval.py` | `agent/workflow/workflow_engine.py` |
| Granularity | per tool call | per task (execute→verify gap) |
| State | ephemeral (in-memory) | DB-persisted (`workflow_approvals`) |
| Resolution | stdin interactive | `/approve` / `/reject` |
| Currently active | always enabled | disabled (`require_approval=False`) |

**Coexistence rules to add:**

When `require_approval=True`:
1. During execute stage: `run_approval_checks` fires per tool call (MEDIUM/HIGH risk tools only).
2. After execute stage: `_gate_approval()` suspends the workflow; user runs `/approve` or `/reject`.
3. Both fire independently. This is intentional: they operate at different granularities.

**ADR rationale to add:**

The requirement "one canonical approval object" means: define clear boundaries and responsibilities for each layer. It does not mean eliminate one layer. Both layers solve different problems:
- Tool-level: real-time per-tool risk gate (before execution).
- Workflow-level: human sign-off on the full execute stage result (after execution).

---

## Validation plan

- Pre-commit: `pre-commit run --all-files` — markdown lint must pass.
- Search: `grep -n "ADR-001\|Canonical Approval" docs/05_agent_06_tool-execution-and-approval.md` — section must exist.
- Visual review: confirm boundary table and coexistence rules are present and accurate.
