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
1. Exact match or prefix match in the built-in command list
2. Plugin commands registered via `@register_command` decorator (lower priority)

Boundary: `line == name` (exact) or `line.startswith(name + " ")` (prefix).

### Module Ownership

| Module | Owns | Does NOT Own |
|--------|------|--------------|
| `command_defs.py` | `CommandDef`, `SubcommandSpec` dataclasses | Command list |
| `command_defs_list.py` | Built-in command definitions | Dispatch logic |
| `registry.py` | Dispatch behavior; imports command list from `command_defs_list` | Command list definition |

> **Future command additions:** add a new `CommandDef(...)` entry to `command_defs_list.py` only.
> Implement the corresponding handler in the appropriate mixin file.

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
| `/mcp status` | HTTP probe to all MCP servers | Displays health table |

### Config / stats category

| Command | Side effects | Related state |
|---|---|---|
| `/config` | None | Display config file paths + values |
| `/stats` | None | Display session metrics |
| `/set temperature <f>` | Updates `ctx.cfg.llm.llm_temperature` + the LLM service's internal temperature field | Immediate LLM effect |
| `/set max_tokens <n>` | Updates `ctx.cfg.llm.llm_max_tokens` | Immediate LLM effect |
| `/reload` | Reloads all config files | Updates `ctx.cfg` and syncs services |

### Context category

| Command | Side effects | Related state |
|---|---|---|
| `/context` | None | Display history size, budget, system prompt, workflow mode, approval-pending state |
| `/compact` | LLM call (compression) | Compresses history immediately |
| `/system [name]` | Updates `history[0]` | `ctx.conv.system_prompt_name` |

### DB category

#### `/db rag` subcommands

| Command | Side effects | Notes |
|---|---|---|
| `/db rag stats` | None | Document/chunk counts (RAG only) |
| `/db rag urls [--lang] [--limit]` | None | List documents via rag-pipeline-mcp |
| `/db rag clean <url>` | Delete document + chunks via rag-pipeline-mcp | Cascaded delete |
| `/db rag rebuild-fts` | Rebuilds `chunks_fts` index | FTS5 rebuild |
| `/db rag vec-rebuild` | None | Rebuild vector index |
| `/db rag reconcile-url <url>` | None | Rebuild FTS/vec for a single URL |
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

> **Note:** `/db rag urls` and `/db rag clean` call rag-pipeline-mcp MCP tools (`rag_list_documents`, `rag_delete_document`) via the agent's tool executor. RAG maintenance commands use `RagMaintenanceService`; session maintenance commands use `DbMaintenanceService`. `session.sqlite` and `workflow.sqlite` are accessed via `SQLiteHelper(target=...)` in code, not through `/db` commands. Schema details: `90_shared_04`.

### Plan category

| Command | Side effects | Related state |
|---|---|---|
| `/plan` | None | Toggle `ctx.conv.plan_mode` |

### Workflow category

| Command | Side effects | Related state |
|---|---|---|
| `/approve [reason]` | Resolves suspended workflow approval as approved | `ctx.turn.pending_approval_id` (DB-lookup fallback when None) |
| `/reject [reason]` | Resolves suspended workflow approval as rejected | `ctx.turn.pending_approval_id` (DB-lookup fallback when None) |

> **Scope:** `/approve` and `/reject` resolve **workflow-level approval gates only** (the `approvals` DB record).
> They do not affect per-tool interactive approval prompts (`tool_approval.run_approval_checks`).
> See [Tool Execution and Approval](05_agent_06_tool-execution-and-approval.md) for the canonical approval model.

#### Startup Recovery

If the agent restarts while a workflow-level approval is pending, the pending state is
automatically detected at startup from the `approvals` database table via
`StateStore.find_latest_pending_approval()`. A startup notice is shown:

```
[workflow] Pending approval from previous session — task=<task_id> approval=<approval_id> reason=<reason>. Use /approve [reason] or /reject [reason].
```

The workflow resumes from the approval gate; no re-execution of prior steps is needed.

**Cross-session guarantee:** `/approve` and `/reject` resolve the latest pending approval
from the `approvals` DB table even when in-memory `ctx.turn.pending_approval_id` is None
(e.g., after a crash). After `/approve` succeeds, `ctx.turn.pending_approval_task_id` is
set for auto-resume — no re-execution of prior steps is needed.

### Debug / audit category

| Command | Side effects | Related state |
|---|---|---|
| `/debug` | None | Toggle `ctx.conv.debug_mode` |
| `/debug verbose\|normal` | Change log level | `structlog` level change |
| `/audit [tail N\|turn <id>\|tool <name>]` | None | Read audit.log |

### RAG / Export category

| Command | Side effects | Related state |
|---|---|---|
| `/rag search <query> [--debug]` | MCP call to rag-pipeline-mcp | None |
| `/compact` | LLM call (compression) | Compresses history immediately |
| `/export [md\|json] [file]` | Write conversation to file or stdout | Markdown or JSON export |

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

## Migration Notes


