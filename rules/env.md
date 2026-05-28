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
| `code` (`qwen2.5-coder-7b`) | 8001 |
| `chat` (`gemma-4-e4b`) | 8002 |
| `embed` | 8003 |
| `web-search-mcp` | 8004 |
| `file-mcp` | 8005 |
| `github-mcp` | 8006 |

## OpenRC service names (`init.d/`)

- `embed-llm`
- `llama-chat-llm`
- `llama-coding-llm`
- `web-search-mcp`
- `file-mcp`
- `github-mcp`
- `llama-agent`

```bash
rc-service <name> status   # check status
rc-service <name> restart  # restart
tail -f /opt/llm/logs/agent.log
tail -f /opt/llm/logs/file-mcp.log
```

## Architecture

- Ingestion pipeline (data flow, FTS5 implementation): `docs/03_ingestion-pipeline.md` §5
- Agent REPL pipeline (MQE → Search → RRF → Rerank): `docs/05_agent-impl.md` §2
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
| `web_search_mcp_server.py` | `web-search-mcp` (port 8004). Brave → Bing → DuckDuckGo fallback. |
| `mcp_server.py` | Base class. `run()` = HTTP; `run_stdio()` = stdin/stdout JSON-RPC (`--stdio` flag). |
| `mcp_models.py` | `CallToolRequest` / `CallToolResponse` Pydantic models. |
| `config_loader.py` | JSON loader that strips `_doc` keys. |
| `logger.py` | `FileHandler` + `StreamHandler` logger for entry scripts. |
| `sqlite_helper.py` | Loads `sqlite-vec`, WAL mode, foreign keys. Usage: `with SQLiteHelper().open(...) as db:` |
| `formatters.py` | `truncate`, `fmt_size`, `fmt_md_link`, `fmt_kvlog`. |
| `create_schema.py` | DB schema init (first run only). Idempotent via `IF NOT EXISTS`. |
| `pipeline_utils.py` | `read_json_file`, `collect_source_files`, `is_already_processed`. |
| `mcp_installer.py` | MCP server scaffold wizard. Called via `/mcp install <name>`. |

Additional notes:
- When adding/removing a module: update `deploy/deploy.sh`.
- New MCP server: add to `mcp_servers` in `config/agent.json`. `_MCP_SERVICE_MAP` in `agent_repl.py` is legacy.
- To use stdio transport: set `"transport": "stdio"` and `"cmd": [...]` in `agent.json`; use `--stdio` flag.
- `db/rrf.sql` is reference SQL only — not used at runtime.

## SQLite schema

| Table | Key columns | Notes |
|---|---|---|
| `documents` | `doc_id` (PK), `url` (UNIQUE), `title`, `lang`, `fetched_at`, `etag`, `last_modified` | `lang`: `ja` or `en`. ETag/Last-Modified for 304 handling. |
| `chunks` | `chunk_id` (PK), `doc_id` (FK CASCADE), `chunk_index`, `content`, `normalized_content` | `normalized_content` for JA only (Sudachi). `NULL` for EN/code. |
| `chunks_vec` | `chunk_id` (PK), `embedding` (`float[384]`) | `sqlite-vec` `vec0` virtual table; little-endian float32 BLOB. |
| `chunks_fts` | `content`, `content_rowid='chunk_id'` | FTS5, `unicode61` tokenizer. Trigger: `COALESCE(normalized_content, content)`. |
| `sessions` | `session_id` (PK), `created_at`, `title` | `title` = first 50 chars of first user input. |
| `messages` | `message_id` (PK), `session_id` (FK CASCADE), `role`, `content`, `tool_calls`, `created_at` | `tool_calls` is JSON string. |
| `notes` | `note_id` (PK), `content`, `created_at` | Injected into system prompt when `auto_inject_notes=true`. |

## Config files

| File | Description |
|---|---|
| `config/common.json` | DB path, `sqlite-vec` `.so` path, embed endpoint |
| `config/agent.json` | LLM URL, RAG params, tool defs, `system_prompt_tool` / `system_prompt_rag` |
| `config/rag_pipeline.json` | Crawl targets, depth/delay, chunk size, stopwords, `embed_workers`, `chunk_overlap` |
| `config/fileop_mcp_server.json` | Allowed root directories for `file-mcp` |
| `config/github_mcp_server.json` | `github-mcp` configuration |
| `config/web_search_mcp_server.json` | `web-search-mcp` configuration |

API keys via OpenRC conf.d (not shell env):

| File | Variables |
|---|---|
| `/etc/conf.d/web-search-mcp` | `BRAVE_API_KEY`, `BING_API_KEY` |
| `/etc/conf.d/github-mcp` | `GITHUB_TOKEN` |

### agent.json key highlights

- `default_mode`: `"chat"` or `"code"`
- `use_mqe` / `use_search` / `use_rrf` / `use_rerank`: disable individual RAG steps
- `masked_fields`: tool argument keys redacted in console/log (default: `["file_content"]`)
- `plan_blocked_tools`: tools blocked when `/plan` mode is active
- `mcp_servers`: per-server transport config (`transport`, `url`, `cmd`, `openrc_service`)
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
| `docs/05_agent-impl.md` | Agent 実装詳細・REPL フロー・クラス API |
| `docs/06_common.md` | 共通モジュール index (→ 以下4ファイルへのリンク集) |
| `docs/06_ref-infra.md` | config_loader / rag_utils / sqlite_helper / logger / formatters |
| `docs/06_ref-mcp.md` | mcp_models / mcp_server / tool_executor |
| `docs/06_ref-rag.md` | agent_rag (RAG パイプライン) |
| `docs/06_ref-agent.md` | agent_session / agent_repl / agent_config / agent_context / cli_view / agent_commands / llm_client / history_manager |

## Deploy commands

```bash
bash deploy/deploy.sh          # copy scripts/ and config/ to /opt/llm/
bash deploy/init_db.sh         # initialize SQLite schema (first run only)
bash deploy/setup_services.sh  # register and start OpenRC services (first run only)
```

## Ingestion pipeline

```bash
source /opt/llm/venv/bin/activate
cd /opt/llm/scripts
python3 web_crawler.py   [--url <url>] [--lang ja|en|auto]
python3 chunk_splitter.py [--file <path>] [--force]
python3 rag_ingester.py   [--force]
```
