# Implementation: Add Turn-State Mutation Table

## Goal

Add explicit turn-state mutation table to `05_agent_03` and persistence timing column to `05_agent_04`.

## Scope

**In:**
- `docs/05_agent_03_turn_and_state_management.md` — add turn-state mutation table
- `docs/05_agent_04_session_and_persistence.md` — add persistence timing column

**Out:** No code changes.

## Assumptions

1. ConvState fields: `messages`, `tool_results`, `current_turn`, `is_processing`, `partial_completion`.
2. SessionState fields: `title`, `created_at`, `last_active_at`, `message_count`.
3. Some state is durable (SQLite), some is ephemeral (in-memory only).

## Implementation

### Target file

`docs/05_agent_03_turn_and_state_management.md`, `docs/05_agent_04_session_and_persistence.md`

### Procedure

1. Confirm ConvState fields:
   ```bash
   grep -rn "class ConvState\|@dataclass" agent/ --include="*.py" | head -10
   grep -rn "is_processing\|tool_results\|current_turn" agent/ --include="*.py" | head -10
   ```
2. Read `docs/05_agent_03_turn_and_state_management.md` to find insertion point.
3. Add turn-state mutation table.
4. Read `docs/05_agent_04_session_and_persistence.md` to find persistence section.
5. Add persistence timing column.

### Method

Bash grep → Read docs → Edit patches.

### Details

**Mutation table for `05_agent_03`:**

```markdown
## Turn-State Mutation Reference

| Field | Mutated When | Durable? | Notes |
|---|---|---|---|
| `messages` | After each LLM/tool call | Yes (SQLite) | Append-only |
| `current_turn` | At turn start | No (in-memory) | Reset to 0 on restart |
| `is_processing` | At turn start (`True`) / end (`False`) | No (in-memory) | SIGTERM guard |
| `tool_results` | After each tool call | Session only | Cleared after turn completes |
| `partial_completion` | On interrupted turn | Logged only | Not persisted to storage |
| `session.title` | On first turn (async) | Yes (SQLite) | Non-blocking; fallback if fails |
| `session.last_active_at` | After each turn | Yes (SQLite) | Updated by session manager |
```

**Persistence timing column for `05_agent_04`:**

Extend the existing state table (if present) with a "When persisted" column showing the timing (e.g., "immediately", "end of turn", "async").

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Mutation table present | `grep -n "Mutated When\|is_processing.*in-memory" docs/05_agent_03_turn_and_state_management.md` | found |
| Persistence column | `grep -n "When persisted\|persistence.*timing" docs/05_agent_04_session_and_persistence.md` | found |
| No code changes | `git diff agent/` | empty |
