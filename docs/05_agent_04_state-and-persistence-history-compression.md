---
title: "Agent State and Persistence"
category: agent
tags:
  - agent
  - agent
  - state
  - persistence
  - session
  - history
related:
  - 05_agent_00_document-guide.md
---

# Agent State and Persistence

sation History and Database

```
ctx.conv.history (in-memory list)
    ↕ synchronized per turn
AgentSession (session.sqlite: sessions + messages)
```

- History is the authoritative source during a session
- Database is the persistent backup
- `/session load <id>` reconstructs `ctx.conv.history` from database
- `delete_last_turn()` removes last 2 rows (up to 2) from DB
- `undo_last_turn()` removes everything from the last `role='user'` message onwards

---

## HistoryManager Compression



`HistoryManager` (`agent/history.py`) manages compression of `ctx.conv.history`.

### Compression trigger

Triggered each turn if either:
- `len(history_chars) > context_char_limit` (default 8000)
- `token_count > context_token_limit` (if > 0)

### Compression selection

`HistorySelectionPolicy.select_turns_to_compress()` selects turns by:
1. Importance scoring (pinned → explicit importance → keyword-based)
2. Category classification:
   - `temporary` (tool role) — highest removal priority
   - `temporary_reasoning` (assistant with tool_calls) — second priority
   - `factual` (system) — preserved
   - `history` (user/assistant text) — normal priority
3. The most recent `history_protect_turns` (default 2) user+assistant pairs are exempt

### Compression result

- Selected old turns → replaced with one LLM summary message
- `CompressResult.compressed_count` = number of messages replaced
- `CompressResult.protected_count` = number of messages skipped (protected)
- `stat_compress_count` incremented

### Compression Persistence Model

After each history compression (automatic or `/compact`), the compressed snapshot is persisted back to `session.sqlite` via `AgentSession.replace_messages()`. This ensures that `/session load` restores a semantically consistent state — the restored history matches what was actually in context before the next LLM call.

Key behaviors:
- Compressed `[Conversation summary]` system messages are persisted as `role=system` rows; they round-trip correctly through `fetch_messages()` → `LLMMessage`.
- Fallback truncation (drop-without-summary) also triggers persistence to keep DB consistent.
- The in-memory `ctx.conv.history` remains the source of truth for the current session; DB persistence is a backup for reload scenarios.
- `/history` and `/export` continue to operate on `ctx.conv.history`; no change needed.
- The `stat_turns` counter and other in-memory stats reset on reload (existing behavior).

**Note**: After a reload of a compressed session, `/undo` operates on the compressed DB rows — the user may undo fewer turns than expected since the original messages were replaced by the summary message.

### Token counting

Priority: (1) LLM `usage.input_tokens` (exact); (2) `/tokenize` endpoint (exact);
(3) `chars // 4` fallback.

### HistoryManager API (key methods)

| Method | Description |
|---|---|
| `count_chars(history)` | Total chars (content + tool_calls JSON) |
| `count_tokens(history, last_input_tokens)` | Sync token estimate |
| `count_tokens_async(...)` | Async token count; returns `(count, is_exact)` |
| `compress(history)` | Compress if over limit; returns `(new_history, CompressResult)` |
| `force_compress(history)` | Compress immediately regardless of limit (`/compact` cmd) |
| `apply_config(...)` | Hot-reload: char_limit, compress_turns, token_limit, tokenize_url |

### Compression Persistence Model

After each history compression (automatic or `/compact`), the compressed snapshot is persisted back to `session.sqlite` via `AgentSession.replace_messages()`. This ensures that `/session load` restores a semantically consistent state — the restored history matches what was actually in context before the next LLM call.

Key behaviors:
- Compressed `[Conversation summary]` system messages are persisted as `role=system` rows; they round-trip correctly through `fetch_messages()` → `LLMMessage`.
- Fallback truncation (drop-without-summary) also triggers persistence to keep DB consistent (`CompressResult.is_fallback=True`).
- The in-memory `ctx.conv.history` remains the source of truth for the current session; DB persistence is a backup for reload scenarios.
- `/history` and `/export` continue to operate on `ctx.conv.history`; no change needed.
- The `stat_turns` counter and other in-memory stats reset on reload (existing behavior).

**Note**: After a reload of a compressed session, `/undo` operates on the compressed DB rows — the user may undo fewer turns than expected since the original messages were replaced by the summary message.

---

## Data Classification

| Data

 type | Scope | Storage | When persisted | Cleared by |
|---|---|---|---|---|
| `ctx.conv.history` | session | in-memory | Per message (async, before LLM call) | `/clear` or session end |
| `ctx.conv.*` flags | session | in-memory | — (not persisted) | session restart |
| `ctx.turn.current_turn_id` | turn | in-memory | — (not persisted) | end of each turn |
| `ctx.stats.*` | session | in-memory | — (reported via `/stats`) | `/clear` |
| `sessions` table | persistent | SQLite | On session create; title async on first turn | `/session delete` |
| `messages` table | persistent | SQLite | Per `AgentSession.save()` call | `/session delete` or `/undo` |
| Memory JSONL / `memories` table | persistent | JSONL + SQLite | On memory extraction (async) | `/memory delete` or `/memory prune` |

---

## Platform Databases

The age

## Related Documents

- `agent`
- `state`
- `persistence`

## Keywords

agent
state
persistence
session
history
