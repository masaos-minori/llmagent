# rules/env.md — Environment, Architecture, and Reference

このファイルは一次情報（docs に記載のない事実）と、詳細を持つ docs へのポインタのみを載せる。手順・値の詳細は該当 docs を参照すること。

## Target environment

- **Python:** 3.13 (`pyproject.toml` `requires-python = ">=3.13"`)
- **Package manager:** uv 一本化。ローカル・本番とも仮想環境を直接 activate せず `uv run python -m ...` 経由で実行する（venv パスを決め打ちしない）
- **DB:** SQLite + `sqlite-vec` 拡張

導入手順・依存パッケージ・llama.cpp ビルド: `docs/02_deployment-part1.md`

```bash
export PATH="$HOME/.local/bin:$PATH"   # uv, fd, ast-grep を使うために追加
```

## Service endpoints and ports

MCP サーバ 8 種のポート一覧・役割: `docs/04_mcp_01_system_overview.md`（表）

上記に含まれないポート:

| Service | Port |
|---|---|
| `agent-llm`（LLM 本体） | 8080 |
| `embed-llm` | 8081 |
| Event Bus (`eventbus.app`) | 8015 |

ポートの正 (SSOT) は各サーバ実装の `http_port` クラス変数（`scripts/mcp_servers/server.py` 基底）と `config/agent.toml` の `[mcp_servers.*]` の `url`。個別の `config/*_mcp_server.toml` にはポート設定を持たない。8011, 8016 は未使用。

## Service management

常駐サービス（`embed-llm`/`agent-llm`/`eventbus`）の起動・ヘルスチェック手順、MCP サーバの subprocess 自動起動: `docs/02_deployment-part1.md` §2.3, §2.4

```bash
tail -f /opt/llm/logs/agent.log
```

## Architecture

6 層構成（トップレベル `scripts/{agent,db,eventbus,mcp_servers,rag,shared}/`）。`.importlinter`（リポジトリ直下）が依存方向を強制する。

```
shared  → external only（リーフ層。他レイヤーに依存しない）
db      → shared
rag     → db, shared
mcp_servers → db, shared
agent   → rag, db, shared, mcp_servers（installer 用途のみ）
eventbus → 他の全レイヤーから完全に独立（shared にすら依存不可）
```

`lint-imports` で違反を検出。各レイヤーの責務・ファイル構成:

| ディレクトリ | エントリポイント docs |
|---|---|
| `scripts/agent/` | `docs/05_agent_00_document-guide.md` |
| `scripts/db/` | `docs/90_shared_00_document-guide.md` |
| `scripts/eventbus/` | `docs/06_eventbus_00_document-guide.md` |
| `scripts/mcp_servers/` | `docs/04_mcp_00_document-guide.md` |
| `scripts/rag/` | `docs/03_rag_00_document-guide.md` |
| `scripts/shared/` | `docs/90_shared_00_document-guide.md` |

ファイル単位の詳細一覧: `docs/01_overview.md`（→ `01_overview-files-*.md`）

Config directory resolution: `scripts/shared/config_loader.py` の `Path(__file__).resolve().parent.parent.parent / "config"`。本番: `/opt/llm/scripts/shared/config_loader.py` → `/opt/llm/config/`。

`deploy/deploy.sh` は `scripts/` を `rsync -av --delete` で丸ごと同期するため、Python ファイルの追加/削除時に `deploy.sh` の更新は不要。一方 `config/*.toml` は依然として個別 `cp` 文で列挙しているため、**新規 config toml を追加したら `deploy.sh` に `cp` 行を追記する**こと。

## SQLite schema

DB は rag.sqlite / session.sqlite / workflow.sqlite / eventbus.sqlite の 4 ファイルに分割。DDL は `scripts/db/schema_sql.py` が SSOT（`db/create_schema.py` の `create_schema()` が rag → session → workflow → eventbus の順に一括作成）。`SQLiteHelper(target)` で切り替える。

テーブル定義・カラム詳細:

| DB | 参照先 |
|---|---|
| `rag.sqlite` | `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part1.md` §5 |
| `session.sqlite` | `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md` §6 |
| `workflow.sqlite` | `docs/90_shared_04_02_db_architecture_and_schema-schema-reference-part2.md` §7 |
| `eventbus.sqlite` | `docs/06_eventbus_03_persistence_schema_and_replay.md` |

DB 構成・接続管理の全体像: `docs/90_shared_04_01_db_architecture_and_schema-overview-and-config.md`。マイグレーション/スケーリング: `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`。

## Config files

各 MCP サーバは自分専用の `*_mcp_server.toml` のみを読み込み、`agent.toml` は読まない（プロセス分離方針。`MCPServer.run_http()` が `ConfigLoader.restrict_to()` で強制）。MCP サーバ↔config ファイルの対応表、API キー env files (`conf.d/`): `docs/04_mcp_06_02_configuration-file-inventory.md`

上記ドキュメントに含まれない config ファイル:

| File | Description |
|---|---|
| `config/agent.toml` | AgentREPL 専用設定。DB パス、embed/llm URL、RAG パラメータ、tool definitions、`mcp_servers.*`、`tool_safety_tiers`、`system_prompts` 等 |
| `config/eventbus.toml` | Event Bus 設定。`port`(8015), `db_path`, `storage_dir`, `offsets_dir`, `deadletter_dir`, `max_retry` |
| `config/crawler.toml` | `rag/ingestion/crawler.py` 専用設定 |
| `config/chunk_splitter.toml` | `rag/ingestion/chunk_splitter.py` 専用設定 |
| `config/ingester.toml` | `rag/ingestion/ingester.py` 専用設定 |
| `config/workflows/default.json` | ワークフロー定義。デプロイ時に存在チェック・スキーマ検証・SHA256 照合が行われる必須アーティファクト |

agent.toml の全設定項目・ホットリロード可否・分類: `docs/05_agent_08_01_configuration-loading-agent-config-part1.md` 以降（`05_agent_08_02〜04`）

## Reference documents

| File | Content |
|---|---|
| `docs/index.md` | ドキュメント全体索引 |
| `docs/01_overview.md` | システム全体のアーキテクチャ・ファイル構成索引 |
| `docs/02_deployment-part1.md` / `-part2.md` | 導入手順・デプロイ |
| `docs/03_rag_00_document-guide.md` | RAG ドキュメントセット入口 |
| `docs/04_mcp_00_document-guide.md` | MCP ドキュメントセット入口 |
| `docs/05_agent_00_document-guide.md` | Agent ドキュメントセット入口 |
| `docs/06_eventbus_00_document-guide.md` | Event Bus ドキュメントセット入口 |
| `docs/90_shared_00_document-guide.md` | shared/DB ドキュメントセット入口 |
| `routing.md` | タスク種別 → ロードすべき skill/docs のルーティング表 |

各ドキュメントセットの詳細な章立ては `routing.md` の「Docs → task mapping」を参照。

## Deploy commands

実行順序・各スクリプトの責務・ワークフロー検証・トラブルシューティング: `docs/02_deployment-part1.md` §2, `docs/02_deployment-part2.md` §3

```bash
bash deploy/build_sqlite_vec.sh   # 初回のみ
bash deploy/deploy.sh
bash deploy/init_db.sh
bash deploy/setup_services.sh
bash deploy/start_agent.sh
```

## Ingestion pipeline

コマンド例・引数・`--force` の挙動・RAG 整合性チェック: `docs/03_rag_05_2-execution-guide.md`
