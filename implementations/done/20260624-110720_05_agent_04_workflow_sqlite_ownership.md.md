# Implementation: Fix workflow.sqlite Ownership Documentation

## Goal

Clarify that `workflow.sqlite` is owned by the orchestrator, not the session manager. Update 3 agent docs.

## Scope

**In:**
- `docs/agent_04_session_and_persistence.md` — fix ownership description
- `docs/agent_09_observability_and_logging.md` — fix ownership reference
- `docs/agent_10_operations_and_deployment.md` — fix operations guidance

**Out:** No code changes.

## Assumptions

1. `workflow.sqlite` is created/owned by `agent/orchestrator.py` (or equivalent workflow module).
2. `sessions.sqlite` (or `agent.sqlite`) is owned by `agent/session_manager.py`.
3. Current docs may incorrectly attribute `workflow.sqlite` to session management.

## Implementation

### Target file

`docs/agent_04_session_and_persistence.md`, `docs/agent_09_observability_and_logging.md`, `docs/agent_10_operations_and_deployment.md`

### Procedure

1. Confirm owner:
   ```bash
   grep -rn "workflow.sqlite\|workflow\.db" agent/ --include="*.py" | head -10
   ```
2. Read ownership section in `agent_04`.
3. Fix ownership attribution: "workflow.sqlite is owned by the orchestrator, not the session manager."
4. Read `agent_09` log section for workflow.sqlite references and fix.
5. Read `agent_10` operations section and fix backup/ops guidance.

### Method

Bash grep to confirm → Read → Edit patches.

### Details

**Ownership clarification table (for `agent_04` and others):**

```markdown
| File | Owner Module | Purpose |
|---|---|---|
| `workflow.sqlite` | `agent/orchestrator.py` | Workflow state: pending / approved / rejected |
| `sessions.sqlite` | `agent/session_manager.py` | Session metadata, titles, message counts |
| `memory.sqlite` | `agent/memory/store.py` | Memory records with embeddings |
| `agent.sqlite` | `db/helper.py` | Tool results, event log |
```

**Fix pattern for all 3 docs:**
- Find any text that says "session manager creates/owns workflow.sqlite" or similar.
- Replace with "workflow.sqlite is owned by `agent/orchestrator.py` (see §Workflow Orchestration)."

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Correct owner in 05_agent_04 | `grep -n "orchestrator.*workflow.sqlite\|workflow.sqlite.*orchestrator" docs/agent_04_session_and_persistence.md` | found |
| No code changes | `git diff agent/` | empty |
