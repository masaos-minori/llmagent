# rules/env.md — Environment, Architecture, and Reference

## Target environment

- **Python:** 3.13 (production venv: `/opt/llm/venv/`; dev venv: `.venv/` managed by uv)
- **DB:** SQLite + `sqlite-vec` extension at `/opt/llm/sqlite-vec/vec0.so`
- **Package manager:** uv (binary at `~/.local/bin/uv`)

Add `~/.local/bin` to `PATH` to access `uv`, `fd`, and `ast-grep`:
```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Service endpoints and ports

| Service | Port |
|---|---|
| `llm` (agent-llm) | 8001 |
| `embed` (embed-llm) | 8003 |
| `web-search-mcp` | 8004 |
| `file-mcp` | 8005 |
| `github-mcp` | 8006 |

## Service management

LLM サービス (エージェント管理 subprocess):
- `embed-llm`
- `agent-llm`
- `llama-agent`

MCP サーバ (ports 8004-8014) はエージェント管理 subprocess として起動。

```bash
tail -f /opt/llm/logs/agent.log
```

## Architecture

- Ingestion pipeline (data flow, FTS5 implementation): `docs/03_ingestion-pipeline.md` §5
- Agent REPL pipeline (MQE → Search → RRF → Rerank): `docs/05_agent-impl-class.md` §1
- MCP transport modes and adding new servers: `docs/04_mcp-protocol.md` §2

Config directory resolution: `Path(__file__).resolve().parent.parent / "config"` — one level above `scripts/`.
In production: `/opt/llm/scripts/../config/` → `/opt/llm/config/`

`deploy/deploy.sh` uses individual `cp` statements. Adding/removing a file under `scripts/` requires updating `deploy.sh`.

## Module decomposition (`scripts/`)

| File | Role |
|---|---|
| `agent_repl.py` | `AgentREPL` coordinator. `_init_components()` builds deps; `_run_turn()` drives LLM/tool loop. |
| `agent_rag.py` | Full RAG pipeline: `RagRepository`, `RagScorer`, `RagLLM`, `RagPipeline`, `SemanticCache`. |
| `agent_commands.py` | `CommandRegistry`. Dispatches slash commands via `dispatch(line)`. |
| `agent_context.py` | `AgentContext`. Per-session mutable state shared by `AgentREPL` and `CommandRegistry`. |
| `agent_config.py` | `AgentConfig` dataclass + `build_agent_config()`. Also defines `McpServerConfig` and `_build_mcp_servers()`. |
| `agent_session.py` | DB operations on `sessions`, `messages`, `notes`. |
| `llm_client.py` | SSE streaming, exponential-backoff retries. |
| `tool_executor.py` | Routes tools to MCP servers. `HttpTransport` and `StdioTransport`. TTL cache. |
| `history_manager.py` | Conversation history tracking and LLM-based compression. |
| `cli_view.py` | Readline setup, RAG progress display, multiline input. |
| `web_crawler.py` | Parallel BFS crawl with 304/ETag/language detection. |
| `chunk_splitter.py` | Splits text into chunks (JA: Sudachi; EN: sentence; code: blank-line; MD: heading). |
| `rag_ingester.py` | Embeds chunks, inserts into SQLite, parallelized via `ThreadPoolExecutor`. |
| `rag_utils.py` | `floats_to_blob`, `validate_url`, `normalize_unicode`. |
| `fileop_mcp_server.py` | `file-mcp` (port 8005). `FileService` enforces security boundaries. |
| `github_mcp_server.py` | `github-mcp` (port 8006). `GitHubService` wraps PyGithub. |
| `web_search_mcp_server.py` | `web-search-mcp` (port 8004). DuckDuckGo only. |
| `mcp_server.py` | Base class. `run()` = HTTP; `run_stdio()` = stdin/stdout JSON-RPC (`--stdio` flag). |
| `mcp_models.py` | `CallToolRequest` / `CallToolResponse` Pydantic models. |
| `config_loader.py` | TOML/JSON loader (stdlib `tomllib`) that strips `_` keys. |
| `logger.py` | `FileHandler` + `StreamHandler` logger for entry scripts. |
| `sqlite_helper.py` | Loads `sqlite-vec`, WAL mode, foreign keys. `target="rag"\|"session"`. Usage: `with SQLiteHelper("session").open(...) as db:` |
| `create_schema.py` | DB schema init. `create_rag_schema()` / `create_session_schema()` / `create_schema()`. |
| `migrate_db.py` | One-shot migration: copies session tables from rag.sqlite → session.sqlite. |
| `formatters.py` | `truncate`, `fmt_size`, `fmt_md_link`, `fmt_kvlog`. |
| `create_schema.py` | DB schema init (first run only). Idempotent via `IF NOT EXISTS`. |
| `pipeline_utils.py` | `read_json_file`, `collect_source_files`, `is_already_processed`. |
| `mcp_installer.py` | MCP server scaffold wizard. Called via `/mcp install <name>`. |

Additional notes:
- When adding/removing a module: update `deploy/deploy.sh`.
- New MCP server: add to `mcp_servers` in `config/agent.toml`. `_MCP_SERVICE_MAP` in `agent_repl.py` is legacy.
- To use stdio transport: set `"transport": "stdio"` and `"cmd": [...]` in `agent.toml`; use `--stdio` flag.
- `db/rrf.sql` is reference SQL only — not used at runtime.

## SQLite schema

DB が 2 ファイルに分割されている。`SQLiteHelper(target)` で切り替える。

**rag.sqlite** (`target="rag"`, `rag_db_path` in `common.toml`):

| Table | Key columns | Notes |
|---|---|---|
| `documents` | `doc_id` (PK), `url` (UNIQUE), `title`, `lang`, `fetched_at`, `etag`, `last_modified` | `lang`: `ja` or `en`. ETag/Last-Modified for 304 handling. |
| `chunks` | `chunk_id` (PK), `doc_id` (FK CASCADE), `chunk_index`, `content`, `normalized_content` | `normalized_content` for JA only (Sudachi). `NULL` for EN/code. |
| `chunks_vec` | `chunk_id` (PK), `embedding` (`float[384]`) | `sqlite-vec` `vec0` virtual table; little-endian float32 BLOB. |
| `chunks_fts` | `content`, `content_rowid='chunk_id'` | FTS5, `unicode61` tokenizer. Trigger: `COALESCE(normalized_content, content)`. |

**session.sqlite** (`target="session"`, `session_db_path` in `common.toml`):

| Table | Key columns | Notes |
|---|---|---|
| `sessions` | `session_id` (PK), `created_at`, `title` | `title` = first 50 chars of first user input. |
| `messages` | `message_id` (PK), `session_id` (FK CASCADE), `role`, `content`, `tool_calls`, `tool_call_id`, `created_at` | `tool_calls` is JSON string. |
| `notes` | `note_id` (PK), `content`, `created_at` | Injected into system prompt when `auto_inject_notes=true`. |
| `tool_results` | `id` (PK), `session_id`, `turn`, `tool_name`, `args_json`, `full_text`, `summary`, `is_error`, `created_at` | `/tool show <id>` で取得可能。 |
| `memory_entries` | `entry_id` (PK), `session_id`, `mem_type`, `content`, `created_at` | `mem_type`: `long_term` \| `task` |
| `memory_vec` | `entry_id` (PK), `embedding` (`float[384]`) | `vec0` virtual table for semantic memory search. |

## Config files

| File | Description |
|---|---|
| `config/common.toml` | DB paths (`rag_db_path`, `session_db_path`), `sqlite-vec` `.so` path, embed endpoint |
| `config/agent.toml` | LLM URL, RAG params, tool defs, `system_prompt_tool` / `system_prompt_rag` |
| `config/rag_pipeline.toml` | Crawl targets, depth/delay, chunk size, stopwords, `embed_workers`, `chunk_overlap` |
| `config/file_read_mcp_server.toml` | Allowed root directories for `file-read-mcp` |
| `config/file_write_mcp_server.toml` | Allowed root directories for `file-write-mcp` |
| `config/file_delete_mcp_server.toml` | Allowed root directories for `file-delete-mcp` |
| `config/github_mcp_server.toml` | `github-mcp` configuration |
| `config/web_search_mcp_server.toml` | `web-search-mcp` configuration |
| `config/shell_mcp_server.toml` | `shell-mcp` configuration |
| `config/rag_pipeline_mcp_server.toml` | `rag-pipeline-mcp` standalone configuration (port 8010) |

API keys via environment or config files:

| File | Variables |
|---|---|
| `conf.d/web-search-mcp` | (no longer needed — DuckDuckGo requires no API key) |
| `conf.d/github-mcp` | `GITHUB_TOKEN` |

### agent.toml key highlights

- `default_mode`: `"chat"` or `"code"`
- `use_mqe` / `use_search` / `use_rrf` / `use_rerank`: disable individual RAG steps
- `masked_fields`: tool argument keys redacted in console/log (default: `["file_content"]`)
- `plan_blocked_tools`: tools blocked when `/plan` mode is active
- `mcp_servers`: per-server transport config (`transport`, `url`, `cmd`)
- `system_prompts`: preset dict; `"default"` used at startup
- `_doc` keys: stripped at runtime by `ConfigLoader`

## Reference documents

| File | Content |
|---|---|
| `docs/00_llm-implementation-guide.md` | Document index |
| `docs/01_overview.md` | Architecture overview |
| `docs/02_deployment.md` | Installation, API key setup |
| `docs/03_ingestion-pipeline.md` | Ingestion pipeline details |
| `docs/04_mcp-servers.md` | MCP server index (→ 以下4ファイルへのリンク集) |
| `docs/04_mcp-web-search.md` | web-search-mcp 詳細 (port 8004) |
| `docs/04_mcp-file.md` | file-mcp 詳細 (port 8005) |
| `docs/04_mcp-github.md` | github-mcp 詳細 (port 8006) |
| `docs/04_mcp-protocol.md` | HTTP API フォーマット / トランスポート / 追加手順 |
| `docs/05_agent.md` | Agent 概要・設定・スラッシュコマンド (L1-344) |
| `docs/05_agent-impl-class.md` | Agent 実装詳細 - クラス API |
| `docs/06_ref-infra.md` | config_loader / rag_utils / sqlite_helper / logger / formatters |
| `docs/06_ref-mcp.md` | mcp_models / mcp_server / tool_executor |
| `docs/06_ref-rag.md` | agent_rag (RAG パイプライン) |

## Deploy commands

```bash
bash deploy/deploy.sh          # copy scripts/ and config/ to /opt/llm/
bash deploy/init_db.sh         # initialize SQLite schema (first run only)
bash deploy/setup_services.sh  # start services (first run only)
```

## Ingestion pipeline

```bash
source /opt/llm/venv/bin/activate
cd /opt/llm/scripts
python3 web_crawler.py   [--url <url>] [--lang ja|en|auto]
python3 chunk_splitter.py [--file <path>] [--force]
python3 rag_ingester.py   [--force]
```
