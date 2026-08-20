# Agent State and Persistence - History Compression

Turn flow $\rightarrow$ [05_agent_02_runtime-architecture.md](05_agent_02_runtime-architecture.md)
Turn flow $\rightarrow$ [05_agent_03_01_turn-processing-flow-overview.md](05_agent_03_01_turn-processing-flow-overview.md)
Data layer (schema) $\rightarrow$ [05_agent_09_01_data-layer-session-db.md](05_agent_09_01_data-layer-session-db.md)

## Purpose

Document the history compression mechanism, including triggers, selection policies, fallback procedures for failures, and the persistence model.

## Design Intent

### Compression Triggers

Triggered during each turn if either of the following conditions is met:

- `len(history_chars) > context_char_limit` (default 8000)
- `token_count > context_token_limit` (if greater than 0)

### Selection of Targets for Compression

`HistorySelectionPolicy.select_turns_to_compress()` selects turns based on the following:

1. **Importance Scoring** — Pinned items $\rightarrow$ Explicit importance $\rightarrow$ Keyword-based
2. **Category Classification**:
   - `temporary` (`tool` role) — Highest priority for deletion
   - `temporary_reasoning` (`assistant` with tool calls) — Second highest priority
   - `factual` (`system`) — Retained
   - `history` (`user`/`assistant` text) — Normal priority
3. **Protection** — The most recent `history_protect_turns` (default 2) user+assistant pairs are excluded from compression.

### Compression Results

- Selected old turns $\rightarrow$ Replaced with a single LLM summary message
- `CompressResult.compressed_count` = Number of messages replaced
- `CompressResult.protected_count` = Number of messages skipped (protected)
- `stat_compress_count` is incremented

### Fallback Decision on Failure

If `HistoryManager.compress()` fails to call the summarization LLM, a `HistoryCompressionError` is raised but caught internally, returning `None` and logging a WARNING. Subsequent branching:

- **If character limit is still exceeded** $\rightarrow$ Falls through to fallback truncation, performing mechanical deletion of low-importance messages without summarization.
- **If character limit is no longer exceeded** $\rightarrow$ Returns as a no-op without modifying history (`CompressResult(compressed_count=0, ...)`).

Fallback truncation sorts messages by `HistorySelectionPolicy.classify_importance()` in ascending order (lowest importance first) and deletes them one by one from candidates that exclude the `system` role and the most recent `protect_turns` pairs until the character limit is met. If the limit cannot be reached even after deleting all messages, it continues processing while issuing a WARNING log. This path sets `CompressResult.is_fallback=True` and increments `HistoryManager.stat_fallback_truncate_count`.

### Compression Persistence Model

After each history compression (automatic or via `/compact`), the compressed snapshot is written back to `session.sqlite` via `AgentSession.replace_messages()`. This ensures that `/session load` restores a semantically consistent state.

Key behaviors:

- The summarized `[Conversation summary]` system message is persisted as a row with `role=system`.
- Fallback truncation (discarding without summarization) also triggers persistence to maintain database consistency.
- The in-memory `ctx.conv.history` remains the source of truth for the current session; database persistence serves as a backup for reloads.
- `/history` and `/export` continue to operate against `ctx.conv.history`; no changes required.
- `stat_turns` counter and other in-memory statistics are reset upon reload (existing behavior).

## Responsibility Boundary

### Token Counting

Priority: (1) LLM's `usage.input_tokens` (accurate), (2) `/tokenize` endpoint (accurate), (3) Fallback to `chars // 4`.

### Data Classification

| Data type | Scope | Storage | When persisted | Cleared by |
|---|---|---|---|---|
| `ctx.conv.history` | Session | In-memory | Per message (asynchronously, before LLM call) | `/clear` or end of session |
| `ctx.conv.*` flags | Session | In-memory | — (not persisted) | Session restart |
| `ctx.turn.current_turn_id` | Turn | In-memory | — (not persisted) | End of each turn |
| `ctx.stats.*` | Session | In-memory | — (reported via `/stats`) | `/clear` |
| `sessions` table | Persistent | SQLite | Upon session creation; title generated asynchronously during the first turn | `/session delete` |
| `messages` table | Persistent | SQLite | Every call to `AgentSession.save()` | `/session delete` or `/undo` |
| Memory JSONL / `memories` table | Persistent | JSONL + SQLite | During memory extraction (asynchronously) | `/memory delete` or `/memory prune` |

## Key Constraints

### Ensuring Protected Pairs

The most recent `history_protect_turns` user+assistant pairs are always protected.

### Enforcing Character Limits

Even during fallback truncation, character limits are strictly enforced.

## Operational Notes

- The `/compact` command is implemented by temporarily setting `char_limit` to `1` and `token_limit` to `0` when calling `compress()`. It does not have a dedicated path for ignoring limits; instead, it reuses existing `compress()` logic by forcing an "over-limit" state.
- `stat_compress_count` and `stat_fallback_truncate_count` are counters maintained by the `HistoryManager` instance itself, not fields under `ctx.stats`. Display commands must access them via `ctx.services.hist_mgr`.

## Known Limitations

- After reloading a session that has been compressed, `/undo` operates on the compressed DB rows. Since original messages were replaced by a summary message, fewer turns may be undoable than the user expects.

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_04_01_state-and-persistence-state-model.md`
- `05_agent_04_03_state-and-persistence-platform-databases.md`

## Keywords

HistoryManager compression
compression trigger
compression selection
data classification
