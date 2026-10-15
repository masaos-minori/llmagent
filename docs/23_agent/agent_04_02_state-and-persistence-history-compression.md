---
title: "Agent State and Persistence - History Compression"
area: agent
tags:
  - agent
  - state-persistence
  - history-compression
related:
  - agent_00_document-guide.md
  - agent_04_01_state-and-persistence-state-model.md
  - agent_04_03_state-and-persistence-platform-databases.md
  - agent_02_runtime-architecture.md
  - agent_03_01_turn-processing-flow-overview.md
  - agent_09_01_data-layer-session-db.md
---
# Agent State and Persistence - History Compression

Turn flow → [agent_02_runtime-architecture.md](agent_02_runtime-architecture.md)
Turn flow → [agent_03_01_turn-processing-flow-overview.md](agent_03_01_turn-processing-flow-overview.md)
Data layer (schema) → [agent_09_01_data-layer-session-db.md](agent_09_01_data-layer-session-db.md)

## Purpose

Document the history compression mechanism, including triggers, selection policies, fallback procedures for failures, and the persistence model.

## Design Intent

### Compression Triggers

Triggered during each turn if either of the following conditions is met:

- `len(history_chars) > context_char_limit` (threshold value: see `config/agent.toml`)
- `token_count > context_token_limit` (if greater than 0)

### Selection of Targets for Compression

`HistorySelectionPolicy.select_turns_to_compress()` selects turns based on the following:

1. **Importance Scoring** — Pinned items → Explicit importance → Keyword-based
2. **Category Classification**:
   - `temporary` (`tool` role) — Highest priority for deletion
   - `temporary_reasoning` (`assistant` with tool calls) — Second highest priority
   - `factual` (`system`) — Retained
   - `history` (`user`/`assistant` text) — Normal priority
3. **Protection** — The most recent `history_protect_turns` user+assistant pairs are excluded from compression.

### Compression Results

- Selected old turns → Replaced with a single LLM summary message
- `CompressResult.compressed_count` = Number of messages replaced
- `CompressResult.protected_count` = Number of messages skipped (protected)
- `stat_compress_count` is incremented

### Fallback Decision on Failure

If `HistoryManager.compress()` fails to call the summarization LLM, a `HistoryCompressionError` is raised but caught internally, returning `None` and logging a WARNING. Subsequent branching:

- **If character limit is still exceeded** → Falls through to fallback truncation, performing mechanical deletion of low-importance messages without summarization.
- **If character limit is no longer exceeded** → Returns as a no-op without modifying history (`CompressResult(compressed_count=0, ...)`).

Fallback truncation sorts messages by `HistorySelectionPolicy.classify_importance()` in ascending order (lowest importance first) and deletes them one by one from candidates that exclude the `system` role and the most recent `protect_turns` pairs until the character limit is met (soft-limit behavior: see Key Constraints, Character Limit Behavior). This path sets `CompressResult.is_fallback=True` and increments `HistoryManager.stat_fallback_truncate_count`.

### Compression Persistence Model

After each history compression (automatic or via `/compact`), the compressed snapshot is written back to `session.sqlite` via `AgentSession.replace_messages()`. This ensures that `/session load` restores a semantically consistent state.

Key behaviors:

- The summarized `[Conversation summary]` system message is persisted as a row with `role=system`.
- Fallback truncation (discarding without summarization) also triggers persistence to maintain database consistency.
- The in-memory `ctx.conv.history` remains the source of truth for the current session; database persistence serves as a backup for reloads.
- `/history` and `/session export` continue to operate against `ctx.conv.history`; no changes required.
- `stat_turns` counter and other in-memory statistics are reset upon reload (existing behavior).
- Each compression updates the undo boundary (`sessions.undo_floor_message_id`) in the same transaction as the snapshot. Messages at or before the boundary, including the summary and the protected recent turns, cannot be undone.

## Responsibility Boundary

### Memory Boundary

History compression changes conversation history only. It does not create,
delete, update, pin, or unpin long-term memory. Memory extraction at session
end operates on the current compressed history; details already removed by
compression are not available for extraction.

### Token Counting

Priority: (1) LLM's `usage.input_tokens` (accurate), (2) `/tokenize` endpoint (accurate), (3) Fallback to the category-aware estimate (see `scripts/shared/token_estimation.py`).

### Data Classification

| Data type | Scope | Storage | When persisted | Cleared by |
|---|---|---|---|---|
| `ctx.conv.history` | Session | In-memory | Per message (asynchronously, before LLM call) | `/clear` or end of session |
| `ctx.conv.*` flags | Session | In-memory | — (not persisted) | Session restart |
| `ctx.conv.undo_floor` | Session | In-memory | Updated at each compression; restored from `sessions` on `/session load` | `/clear` (reset to 0) |
| `ctx.turn.current_turn_id` | Turn | In-memory | — (not persisted) | End of each turn |
| `ctx.stats.*` | Session | In-memory | — (reported via `/stats`) | `/clear` |
| `sessions` table | Persistent | SQLite | Upon session creation; title generated asynchronously during the first turn; compression boundary for `/undo` updated at each compression | `/session delete` |
| `messages` table | Persistent | SQLite | Every call to `AgentSession.save()` | `/session delete` or `/undo` |
| Memory JSONL / `memories` table | Persistent | JSONL + SQLite | During memory extraction (asynchronously) | `/memory delete` or `/memory prune` (not cleared by `/session delete`) |

## Key Constraints

### Ensuring Protected Pairs

The most recent `history_protect_turns` user+assistant pairs are always protected.

### Character Limit Behavior

Fallback truncation drops only unprotected messages, lowest importance first, until the character limit is met. The `system` messages and the protected recent turns are never dropped, so when they alone exceed the limit the limit is a soft limit: processing continues and a WARNING is logged. Protected messages are never dropped silently to reach the limit.

## Operational Notes

- The `/compact` command calls `HistoryManager.force_compress()`, which temporarily sets `char_limit` to `1` and `token_limit` to `0`, calls `compress()`, and then restores the original limits. It has no separate compression path; it reuses `compress()` by forcing an "over-limit" state.
- `stat_compress_count` and `stat_fallback_truncate_count` are counters maintained by the `HistoryManager` instance itself, not fields under `ctx.stats`. Display commands must access them via `ctx.services.hist_mgr`.

## Known Limitations

- Memory extraction at session end operates on the current conversation history. Details already removed by history compression are not available for extraction.

## Keywords

- HistoryManager compression
- compression trigger
- compression selection
- data classification
