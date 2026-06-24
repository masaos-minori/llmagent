# Implementation: Canonical Partial-Completion Model in Agent Docs

## Goal

Define a canonical "partial-completion / diagnostics" model in `05_agent_03` and apply cross-references in the other 4 affected agent docs.

## Scope

**In:**
- `docs/05_agent_03_turn_and_state_management.md` — add canonical partial-completion model
- `docs/05_agent_04_session_and_persistence.md` — update to reference canonical model
- `docs/05_agent_09_observability_and_logging.md` — add diagnostics output spec
- `docs/05_agent_10_operations_and_deployment.md` — update operator guidance
- `docs/05_agent_17_troubleshooting_and_diagnostics.md` — update troubleshooting flow

**Out:** No code changes.

## Assumptions

1. "Partial completion" = tool sequence interrupted mid-run (SIGTERM, max-turns, LLM refusal, tool error).
2. ConvState tracks `is_processing` and current turn index.
3. `05_agent_03` is the canonical home; others cross-reference it.

## Implementation

### Target file

`docs/05_agent_03_turn_and_state_management.md` (primary), 4 others (cross-reference only)

### Procedure

1. Read `agent/repl.py` or equivalent for how partial completion state is tracked (ConvState fields).
2. Read `docs/05_agent_03_turn_and_state_management.md` to find insertion point.
3. Add canonical model section to `05_agent_03`.
4. For each of the other 4 docs:
   a. Read the relevant section.
   b. Add cross-reference: "partial completion model については `05_agent_03` §Partial-Completion Model を参照。"

### Method

Bash grep for ConvState → Read docs → Edit patches.

### Details

**Canonical partial-completion model (add to `05_agent_03`):**

```markdown
## Partial-Completion Model

A partial completion occurs when a tool sequence is interrupted before all steps complete.

| Trigger | `is_processing` | Recoverable? | Log key |
|---|---|---|---|
| SIGTERM received | True → False | Yes (state persisted) | `partial_completion trigger=sigterm` |
| `max_turns` exhausted | True → False | Yes (restart resumes) | `max_turns_reached turns=N` |
| LLM refusal | True → False | Depends on context | `llm_refusal tool=X` |
| Tool error (unrecoverable) | True → False | No | `tool_error_unrecoverable tool=X` |

On partial completion:
1. `is_processing` is set to `False`
2. Current tool chain position is logged
3. The session message history is persisted (durable)
4. In-progress tool results are NOT persisted (ephemeral)
```

**Cross-references to add in other 4 docs:**
- `05_agent_04`: In §Session Persistence — "partial completion 時の永続化挙動については `05_agent_03` §Partial-Completion Model を参照。"
- `05_agent_09`: In §Log Schema — add `partial_completion` log key to log key table.
- `05_agent_10`: In §Operator Guidance — "partial completion の監視については `05_agent_03` §Partial-Completion Model を参照。"
- `05_agent_17`: In §Troubleshooting Flow — add partial completion step.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Canonical model defined | `grep -n "Partial-Completion Model" docs/05_agent_03_turn_and_state_management.md` | found |
| Cross-reference in 05_agent_04 | `grep -n "05_agent_03.*[Pp]artial\|[Pp]artial.*05_agent_03" docs/05_agent_04_session_and_persistence.md` | found |
| No code changes | `git diff agent/ shared/` | empty |
