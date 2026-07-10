---
title: "Agent CLI and Commands"
category: agent
tags:
  - agent
  - agent
  - cli
  - commands
  - repl
  - slash-commands
related:
  - 05_agent_00_document-guide.md
---

# Agent CLI and Commands

### Memory category

| Command | Side effects | Related state |
|---|---|---|
| `/memory list [semantic\|episodic] [n]` | None | Display memory entries |
| `/memory search <query>` | None | FTS5 search over memories |
| `/memory show <id>` | None | Full memory entry display |
| `/memory pin <id>` | UPDATE pinned flag | Entry injected at every session start |
| `/memory unpin <id>` | UPDATE pinned flag | Remove session-start injection |
| `/memory delete <id>` | DELETE entry | Immediate |
| `/memory prune [days]` | DELETE entries older than N days | Uses `memory_retention_days` default |
| `/memory status` | None | Memory mode label (e.g., Hybrid mode / Degraded mode / Memory layer disabled), embedding status, circuit state, retrieval mode; works when memory disabled |
| `/memory check-consistency` | None | Compare JSONL, SQLite, FTS5, and vec row counts |
| `/memory rebuild [--dry-run]` | DELETE + INSERT all memories from JSONL | JSONL is canonical source; clears and re-inserts SQLite |

### MDQ category

| Command | Side effects | Related state |
|---|---|---|
| `/mdq status` | None | Display health and index statistics (calls `stats` MCP tool) |
| `/mdq index <path> [--force]` | Index file/directory | mdq.sqlite updated |
| `/mdq refresh <path> [--force]` | Incremental refresh for changed files | mdq.sqlite updated |
| `/mdq search <query> [--limit N] [--path-prefix PATH] [--mode bm25\|grep]` | FTS5 search | None |
| `/mdq outline <path> [--max-depth N]` | None | Display heading hierarchy |
| `/mdq get <chunk_id> [--with-neighbors]` | None | Display chunk content |
| `/mdq grep <pattern> [--path PATH] [--max-chars N] [--context-before N] [--context-after N]` | Regex search over chunks | None |

> **Note:** All /mdq commands call mdq-mcp MCP tools (port 8013) via the agent's tool executor. MDQ uses `mdq.sqlite` (separate from `rag.sqlite`). See [MDQ vs RAG Boundary](04_mcp_05_security_and_safety_model.md#mdq-vs-rag-boundary) for guidance on when to use MDQ vs RAG.

### Plugin category

| Command | Side effects | Related state |
|---|---|---|
| `/plugin status` | None | Display plugin load results (loaded, failed, conflicts) |

### Other category

| Command | Side effects | Related state |
|---|---|---|
| `/help` | None | Show this help output |

---

## Hot-Reload Scope (`/re

## Related Documents

- `agent`
- `cli`
- `commands`

## Keywords

agent
cli
commands
repl
slash-commands
