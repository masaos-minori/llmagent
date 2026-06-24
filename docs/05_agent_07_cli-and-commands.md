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
| `/context` | None | Display history size, budget, system prompt, workflow mode, approval-pending state |
| `/compact` | LLM call (compression) | Compresses history immediately |
| `/system [name]` | Updates `history[0]` | `ctx.conv.system_prompt_name` |

### DB category

#### Flat forms (compatibility aliases)

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

#### `/db rag` subcommands

| Command | Side effects | Notes |
|---|---|---|
| `/db rag stats` | None | Document/chunk counts (RAG only) |
| `/db rag urls [--lang] [--limit]` | None | List documents via rag-pipeline-mcp |
| `/db rag clean <url>` | Delete document + chunks via rag-pipeline-mcp | Cascaded delete |
| `/db rag rebuild-fts` | Rebuilds `chunks_fts` index | FTS5 rebuild |
| `/db rag recover [backup-path]` | Integrity check; restore from backup if corrupt | RAG only |
| `/db rag consistency` | None | Chunks/FTS/vector index sync check |

#### `/db session` subcommands

| Command | Side effects | Notes |
|---|---|---|
| `/db session stats` | None | Session/message counts |
| `/db session health` | None | journal_mode / integrity / page stats |
| `/db session checkpoint [MODE]` | WAL checkpoint | Flush WAL to main DB |
| `/db session vacuum` | VACUUM | Recover free pages |
| `/db session purge [--max-sessions N] [--max-age-days N]` | DELETE old sessions | Based on count or age |
| `/db session recover [backup-path]` | Integrity check; restore from backup if corrupt | Session only |

> **Note:** `/db rag urls` and `/db rag clean` call rag-pipeline-mcp MCP tools (`rag_list_documents`, `rag_delete_document`) via the agent's tool executor. RAG maintenance commands use `RagMaintenanceService`; session maintenance commands use `DbMaintenanceService`. Flat `/db <subcmd>` forms are compatibility aliases that route to both services. `session.sqlite` and `workflow.sqlite` are accessed via `SQLiteHelper(target=...)` in code, not through `/db` commands. Schema details: `90_shared_04`.

### Tool / plan category

| Command | Side effects | Related state |
|---|---|---|
| `/tool list` | None | Display saved tool result list |
| `/tool show <id>` | None | Display full tool result |

> **Note**: `/tool show <id>` retrieves from `ToolResultStore`. It does not read from the `messages` table.
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
| `/memory status` | None | Embedding enabled, circuit state, retrieval mode; works when memory disabled |
| `/memory check-consistency` | None | Compare JSONL, SQLite, FTS5, and vec row counts |
| `/memory rebuild [--dry-run]` | DELETE + INSERT all memories from JSONL | JSONL is canonical source; clears and re-inserts SQLite |

---

## Hot-Reload Scope (`/reload`)

`/reload` loads all 12 base config files (see [Configuration doc](05_agent_08_configuration.md)) and applies changes where possible. Startup-only settings are detected but not applied.

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
Deferred (next connection): [1 items]
  [DEFER] - mcp/server2.auth_token
Startup-only (ignored): [1 items]
  [STARTUP-ONLY] - use_memory_layer
```

If nothing changed: `No changes detected.`
If all changes applied: `Config reloaded — all changes applied`
If the file cannot be read: `Reload failed (I/O error): <message>`

### Reload classification summary

| Category | `/reload` output tag | Description |
|---|---|---|
| Hot-reloadable | `[OK]` | Applied immediately to the running process |
| Deferred | `[DEFER]` | Stored in cfg; effective on next connection/subprocess start |
| Restart-required | `[RESTART]` | Requires full agent restart |
| Startup-only | `[STARTUP-ONLY]` | Read once at boot; ignored by `/reload` even if changed |
| Skipped | `[SKIP]` | New MCP server — restart required |

See [Configuration: Config file reload eligibility](05_agent_08_configuration.md#config-file-ownership-and-hot-reload-eligibility) for the full per-field classification matrix.

---

## Maintaining the Command List

When adding a new slash command:

1. Register it in `agent/commands/registry.py` (exact name + prefix + handler method reference)
2. Implement the handler in the relevant `cmd_*.py` module (or a new file)
3. Write a unit test: `tests/test_cmd_{name}.py`
4. Update the command summary table in §Slash Command Reference in this doc
5. Update the routing table in `05_agent_00_document-guide.md` if the command is a major feature
6. If the command is operator-facing (e.g., `/stats`, `/reload`, `/db`): update `05_agent_10` §Operational Verification

> Command summary tables in docs are maintained manually. There is no auto-generation.
> Omitting steps 4–6 causes docs to drift — treat them as part of the definition-of-done for any new command.
