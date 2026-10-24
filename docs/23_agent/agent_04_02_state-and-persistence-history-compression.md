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

`HistorySelectionPolicy.select_turns_to_compress()` groups the non-`system` messages into turn units and selects
whole units:

1. **Unit grouping** — a unit starts at a `user` message and holds every `assistant` and `tool` message until the
   next `user` message; messages before the first `user` message form a leading unit, so a `tool` row whose
   `assistant` message was compressed in an earlier cycle is a unit of its own. Concatenating the units reproduces
   the input exactly.
2. **Oldest-first selection** — whole units are taken from the front until the cumulative message count reaches
   `context_compress_turns * 2`; the last unit may overshoot it, so `compressed_count` can exceed the quota.
   `to_compress` and `remaining` are returned in history order.
3. **Pinned units** — a unit containing a message with the `pinned` key set is never selected and stays in
   `remaining` in place.
4. **Protection** — whole units are protected from the end until the cumulative message count reaches
   `history_protect_turns * 2`; the boundary rounds outward and never splits a unit.
5. **System messages** — every `system` message is split out before selection and is never a candidate; summary
   rows are taken out of them and recompressed with the transcript (see Compression Results).
6. **No selection** — returns `None` when no whole unit can be taken, and `compress()` then logs a skip warning
   without modifying history.

Selection identifies messages by unit position, never by value equality, so
`len(system_msgs) + len(to_compress) + len(remaining) == len(history)` for every input and two messages with
identical content are both accounted for. Importance scoring does not order selection; it orders fallback drops (see
Fallback Decision on Failure).

### Compression Results

The selected units are replaced by exactly one `system` message whose content starts with `[Conversation summary]`.
The previous summary text is handed to the summariser in a `PREVIOUS SUMMARY:` block ahead of the transcript, and
the old summary row is removed, so the summary is carried forward in place instead of accumulating rows: an input
that already holds several summary rows produces one. `HistoryManager`'s compression counter increments, and
`CompressResult` reports `compressed_count` (messages replaced), `protected_count` (retained turn messages),
`summary_added=True` and `summary_chars` (new) (the length of the new summary). The INFO log names `summary_chars` (new), and a
WARNING is logged when `summary_chars >= count_chars(to_compress)` — the summary is not smaller than the messages it
replaced. The relative comparison is used because the summariser input caps every message at 300 characters
(`_build_history_text()`), which is what let a 16-message history produce a 1296-character summary block.

### Fallback Decision on Failure

If `HistoryManager.compress()` fails to call the summarization LLM, a `HistoryCompressionError` is raised but caught
internally, returning `None` and logging a WARNING. Subsequent branching:

- **If character limit is still exceeded** → Falls through to fallback truncation, dropping whole turn units
  without summarization.
- **If character limit is no longer exceeded** → Returns as a no-op without modifying history
  (`CompressResult(compressed_count=0, ...)`).

Fallback truncation protects every `system` message plus the whole units covering the last `history_protect_turns`
pairs, groups the remaining candidates into whole units, orders them by `HistorySelectionPolicy.group_importance()`
(the highest `classify_importance()` score inside the unit) ascending, and deletes one whole unit per iteration from
candidates that exclude the `system` role and the protected units until the character limit is met or a further drop
would leave fewer than one message (soft-limit behavior: see Key Constraints, Character Limit Behavior). A
`user`/`assistant` unit and its `tool` results are never split, so no `tool` row is orphaned. This path sets
`CompressResult.is_fallback=True`, `summary_added=False` and `summary_chars=0`, reports `compressed_count` as the
number of dropped messages, and increments `HistoryManager.stat_fallback_truncate_count`.

### Compression Persistence Model

After each history compression (automatic or via `/compact`), the compressed snapshot is written back to `session.sqlite` via `AgentSession.replace_messages()`. This ensures that `/session load` restores a semantically consistent state.

Key behaviors:

- The summarized `[Conversation summary]` system message is persisted as a row with `role=system`.
- Fallback truncation (discarding without summarization) also triggers persistence to maintain database consistency.
- The in-memory `ctx.conv.history` remains the source of truth for the current session; database persistence serves as a backup for reloads.
- `/history` and `/session export` operate against `ctx.conv.history`.
- In-memory statistics such as `stat_turns` are reset upon reload.
- Each compression updates the undo boundary (`sessions.undo_floor_message_id`) in the same transaction as the snapshot. Messages at or before the boundary, including the summary and the protected recent turns, cannot be undone.

## Responsibility Boundary

### Memory Boundary

History compression changes conversation history only. It does not create,
delete, update, pin, or unpin long-term memory. Memory extraction at session
end operates on the current compressed history; details already removed by
compression are not available for extraction.

### Token Counting

`count_tokens_async()` prefers: (1) an exact `last_input_tokens` value supplied by the caller, (2) the `/tokenize`
endpoint when `tokenize_url` is set, (3) the category-aware estimate in `scripts/shared/token_estimation.py` — 4.0
characters per token for text, 2.5 for serialized tool calls, 3.5 for `system` messages. The compression trigger
consults tokens only when the character limit is not already exceeded and `context_token_limit` is greater than 0.
It never supplies `last_input_tokens`, and `config/agent.toml` sets `tokenize_url = ""`, so the trigger compares the
category-aware estimate against `context_token_limit`. The exact per-turn count reaches `count_tokens()` only from
`scripts/agent/services/context_view.py`, which passes the previous turn's `last_input_tokens` for the pre-turn
decision.

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

The last `history_protect_turns` user+assistant pairs are protected as whole units: the boundary rounds outward to
the start of the unit it enters, and `select_turns_to_compress()` and `_build_protected_ids()` apply the same rule so
selection and fallback protection agree. A unit containing a pinned message is never compressed and never dropped.

### Character Limit Behavior

Fallback truncation drops only unprotected whole units, lowest importance first, until the character limit is met or
a further drop would leave fewer than one message. The `system` messages (including the summary) and the protected
recent units are never dropped, so when they alone exceed the limit the limit is a soft limit: processing continues
and a WARNING is logged. Protected messages are never dropped silently to reach the limit. Individual messages can
also exceed `char_limit`.

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
