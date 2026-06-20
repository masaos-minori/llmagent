# Agent CLI and Commands

- System overview → [05_agent_01_system-overview.md](05_agent_01_system-overview.md)

## Purpose

Document the REPL input/output model, CLIView responsibilities, multiline input,
and all slash command categories with their purpose and side effects.

---

## REPL Input/Output Model

- **Prompt:** `agent>` (no session) or `agent[:#N]>` (N = session_id)
- **Normal input:** any text → forwarded to `Orchestrator.handle_turn()`
- **Slash commands:** lines starting with `/` → `CommandRegistry.dispatch(line)`
- **Multiline input:** line ending with `\` → continues with `... ` prompt
- **EOF / Ctrl-D:** graceful shutdown
- **Ctrl-C:** interrupts current line; does not exit REPL

---

## CLIView (`agent/cli_view.py`)

Presentation layer only. Injected as callbacks into components.

### Callbacks

| Callback | Injected into | Called when |
|---|---|---|
| `write_token(token)` | `LLMClient(on_token=...)` | Each SSE token arrives |
| `write_compress_notice(n)` | `HistoryManager(on_compress=...)` | History compressed |
| `write_turn_start()` | `Orchestrator(on_turn_start=...)` | Before each tool-loop turn |
| `write_turn_end()` | `Orchestrator(on_turn_end=...)` | After final LLM answer |
| `write_llm_error(e)` | `Orchestrator(on_error=...)` | LLM request failure |

### Key methods

| Method | Output |
|---|---|
| `setup_readline()` | Tab completion (slash commands), emacs edit mode, history file load |
| `write_progress(msg)` | `  [rag] {msg:<24}` in-place overwrite (`\r`) |
| `clear_progress()` | Erase progress line with spaces |
| `write_warning(msg)` | `[warn] {msg}` |
| `write_startup_banner(chunk_count, n_tools)` | `DB: {n} chunks \| Tools: {n}` |
| `write_history()` | Save readline history to `~/.agent_history` (max 1000 entries) |
| `async read_multiline(loop, first_line)` | Collect `\`-terminated lines; join with `\n` |

### Protocols (for testing)

`Writer` protocol (output operations) and `Reader` protocol (multiline input).
Tests can inject alternative implementations instead of the real CLIView.

---

## CommandRegistry (`agent/commands/registry.py`)

All slash commands dispatched by `CommandRegistry.dispatch(line)`.

Lookup order:
1. Exact match or prefix match in `_COMMANDS` list (built-in)
2. Plugin commands via `_dispatch_plugin()` (lower priority)

Boundary: `line == name` (exact) or `line.startswith(name + " ")` (prefix).

---

## Slash Command Reference

### Session category

| Command | Side effects | Related state |
|---|---|---|
| `/session list [n]` | None | Read `sessions` table |
| `/session load <id>` | Replaces `ctx.conv.history` | `ctx.session.session_id` updated |
| `/session rename <title>` | UPDATE `sessions.title` | None |
| `/session delete <id>` | DELETE session + messages (CASCADE) | Cannot delete current session |
| `/clear [new]` | Resets history; clears stats + cache | `new` → new DB session started |
| `/undo` | Pops last user+assistant turn from history + DB | Also removes memory injections |
| `/history [n]` | None | Display last N user/assistant messages |
| `/export [md\|json] [file]` | File write (if filename given) | None |

### MCP category

| Command | Side effects | Related state |
|---|---|---|
| `/mcp` | HTTP probe to all MCP servers | Displays health table |
| `/mcp install <name>` | Creates scaffold files | New server files + config snippets |

### Config / stats category

| Command | Side effects | Related state |
|---|---|---|
| `/config` | None | Display config file paths + values |
| `/stats` | None | Display session metrics |
| `/set temperature <f>` | Updates `ctx.cfg.llm.llm_temperature` + `ctx.services.llm._temperature` | Immediate LLM effect |
| `/set max_tokens <n>` | Updates `ctx.cfg.llm.llm_max_tokens` | Immediate LLM effect |
| `/reload` | Reloads all config files | Updates `ctx.cfg` and syncs services |

### Context category

| Command | Side effects | Related state |
|---|---|---|
| `/context` | None | Display history size, budget, system prompt |
| `/compact` | LLM call (compression) | Compresses history immediately |
| `/system [name]` | Updates `history[0]` | `ctx.conv.system_prompt_name` |

### DB category

| Command | Target DB | Side effects | Related state |
|---|---|---|---|
| `/db help` | RAG + Session | None | Shows subcommand table |
| `/db stats` | RAG + Session | None | Document/chunk/session/message counts |
| `/db urls [--lang] [--limit]` | RAG | None | List registered documents via rag-pipeline-mcp |
| `/db clean <url>` | RAG | Delete document + chunks via rag-pipeline-mcp | Cascaded delete |
| `/db rebuild-fts` | RAG | Rebuilds `chunks_fts` index | FTS5 rebuild |
| `/db health` | Session | None | journal_mode / integrity / page stats |
| `/db checkpoint [MODE]` | Session | WAL checkpoint | Flush WAL to main DB |
| `/db vacuum` | Session | VACUUM | Recover free pages |
| `/db purge [--max-sessions N] [--max-age-days N]` | Session | DELETE old sessions | Based on count or age |
| `/db recover [backup-path]` | RAG | Integrity check; restore from backup if corrupt | Destructive if corrupt |
| `/db consistency` | RAG | None | Chunks/FTS/vector index sync check |

> **Note:** `/db urls` and `/db clean` call rag-pipeline-mcp MCP tools (`rag_list_documents`, `rag_delete_document`) via the agent's tool executor. Other `/db` commands use `DbMaintenanceService` for direct SQLite access. `session.sqlite` and `workflow.sqlite` are accessed via `SQLiteHelper(target=...)` in code, not through `/db` commands. Schema details: `06_shared_04`.

### Tool / plan category

| Command | Side effects | Related state |
|---|---|---|
| `/tool list` | None | Display saved tool result list |
| `/tool show <id>` | None | Display full tool result |
| `/plan` | None | Toggle `ctx.conv.plan_mode` |

### Workflow category

| Command | Side effects | Related state |
|---|---|---|
| `/approve [reason]` | Resolves suspended workflow approval as approved | `ctx.turn.pending_approval_id` |
| `/reject [reason]` | Resolves suspended workflow approval as rejected | `ctx.turn.pending_approval_id` |

### Note category

| Command | Side effects | Related state |
|---|---|---|
| `/note add <text>` | INSERT into `notes` | Affects system prompt if `auto_inject_notes=True` |
| `/note list` | None | Display all notes |
| `/note delete <id>` | DELETE from `notes` | None |

### Debug / audit category

| Command | Side effects | Related state |
|---|---|---|
| `/debug` | None | Toggle `ctx.conv.debug_mode` |
| `/debug audit` | None | Display audit.log tail |
| `/debug verbose\|normal` | Change log level | `structlog` level change |
| `/audit [tail N\|turn <id>\|tool <name>]` | None | Read audit.log |

### Ingest / RAG category

| Command | Side effects | Related state |
|---|---|---|
| `/ingest <url\|path> [lang] [--snippets-only]` | Web crawl + DB insert | rag.sqlite updated |
| `/rag search <query> [--debug]` | MCP call to rag-pipeline-mcp | None |
| `/compact` | LLM call (compression) | Compresses history immediately |

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

---

## Hot-Reload Scope (`/reload`)

`/reload` loads `common.toml` and `agent.toml` and applies changes immediately.

### Output format

```
Config reloaded — some changes require restart
WARNING: Some settings require restart to take effect.
Restart required: [1 items]
  [RESTART] - server1
Applied (runtime): [3 items]
  [OK] - llm
  [OK] - hist_mgr
  [OK] - tools
```

If nothing changed: `No changes detected.`
If all changes applied: `Config reloaded — all changes applied`
If the file cannot be read: `Reload failed (I/O error): <message>`

### What changes immediately vs. requires restart

| Reloadable at runtime | Requires restart |
|---|---|
| `context_char_limit`, `context_compress_turns` | transport type (http/stdio) |
| `llm_max_retries`, `retry_base_delay` | embed model dimension |
| `tool_cache_ttl` | DB paths |
| `temperature`, `max_tokens` (from config) | plugin directory |
| SSE settings (heartbeat_timeout, etc.) | New MCP server entries |
| Approval rules, protected paths | |
| MCP server URLs (HTTP only) | |
| System prompts | |
