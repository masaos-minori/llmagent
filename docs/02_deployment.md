title: "Deployment Guide (Part 1)"
category: deployment
tags:
  - deployment
  - environment
  - setup
related:
  - 01_overview.md
source:
  - 02_deployment.md


# 環境構築・サービス起動

## Embedding: multilingual-E5-small (384 dim)

### 1.1 Gentoo Linux パッケージ導入

OSのパッケージ導入手順については、[docs/02_deployment-provisioning.md](docs/02_deployment-provisioning.md) を参照してください。

> Python の `sqlite3` モジュールがロード拡張に対応していない場合:
> ```bash
> echo 'dev-lang/python sqlite' >> /etc/portage/package.use/python
> emerge --ask dev-lang/python
> ```

### 1.2 Python 環境構築 (uv を使用)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync --dev --system-certs
```

依存関係の管理は `pyproject.toml`/`uv.lock` に一本化されている(`requirements.txt`は存在しない)。
`uv sync`が実行時・開発時の全依存パッケージを導入する。

### 1.3 llama.cpp のビルド

ビルド手順については、[docs/02_deployment-provisioning.md](docs/02_deployment-provisioning.md) を参照してください。

### 1.4 LLM モデルの取得

モデルファイルは `/opt/llm/models/` に配置します。ファイル名は、各サービスの構成（`model-path` 等）で使用される名称と一致させる必要があります。

> **Canonical source** — このテーブルがモデルファイル名の正典です。`docs/01_overview-files-01-build.md` と `docs/03_rag_05_1-configuration-reference.md` はここを参照します。

| モデル | ファイル名 |
|---|---|
| multilingual-e5-small (埋め込み) | multilingual-e5-small-Q8_0.gguf |
| gemma-4-e4b-it (LLM) | gemma-4-e4b-it-Q4_K_M.gguf |
| Qwopus3.6-35B-A3B-v1 (LLM) | Qwopus3.6-35B-A3B-v1-MTP-Q4_K_M.gguf |

---

## 2. サービス設定

### 2.1 Building sqlite-vec (first time only)

SQLite vector approximate nearest neighbor (KNN: K-Nearest Neighbor) extension. Provides vector embedding storage and similarity search via the `vec0` virtual table.

```bash
bash deploy/build_sqlite_vec.sh
```

Install path: `/opt/llm/sqlite-vec/vec0.so` (must match `sqlite_vec_so` in `agent.toml`)
> ※以前のドキュメントおよびスクリプトでは config/common.toml と記載されていましたが、現在は config/agent.toml に修正されています。

### 2.2 Deploying scripts

`deploy/deploy.sh` performs bulk copying of scripts, config files, and SQL files.

```bash
bash deploy/deploy.sh
```

deploy.sh copies the runtime artifacts required for production operation (dependency definitions, scripts, configuration, and schemas) into `/opt/llm/` and creates the necessary directory structure. For exact details, refer to the comments in `deploy/deploy.sh`.

**Workflow artifact responsibilities (deploy.sh):**
- Checks that `config/workflows/default.json` exists — aborts before any copy if missing
- Validates the workflow definition (parseable JSON, required fields/stages/retry-policy) via `python -m agent.workflow.validate`
- Copies `config/workflows/` to `/opt/llm/config/workflows/`
- Prints workflow name, version, stage list, and SHA256 checksums (source and deployed); aborts if the checksums differ

The workflow definition is a **required workflow deployment artifact**:
source `config/workflows/default.json` → deployed to `/opt/llm/config/workflows/default.json`.
There is no disable, fallback, or workflow-optional mode.

### 2.3 Registering and starting LLM services

`deploy/setup_services.sh` initializes the LLM services.

MCP servers (ports 8004-8014) auto-start as agent-managed subprocesses on agent startup.

**Workflow pre-flight responsibilities (setup_services.sh):**
- Re-checks that the deployed workflow definition (`/opt/llm/config/workflows/default.json`) exists and re-validates it
- Re-checks that `workflow.sqlite` exists with all required tables and a matching schema version
- Services (Event Bus, LLM, MCP) are started **only if** all workflow checks pass — a failure here aborts before any service is spawned

```bash
bash deploy/setup_services.sh
```

サービス起動後、embed-llm/agent-llmそれぞれについてヘルスチェックエンドポイントへの疎通を確認する。具体的なコマンド例は [docs/02_deployment-operations.md](docs/02_deployment-operations.md) を参照。

### 実装上の補足(起動方法)

`deploy/start_agent.sh` は `/opt/llm/pyproject.toml` の有無で本番(`/opt/llm`)/開発(リポジトリルート)を自動判別し、当該ルートで `python -m agent` (`scripts/agent/__main__.py`)を実行する。(Explicit in code)

> API キーの設定:
> - Web 検索: DuckDuckGo — API キー不要
> - GitHub 操作: GITHUB_TOKEN をシェルで export するか、起動前に conf.d/github-mcp を source する

### 2.4 MCP サーバの確認

MCP サーバはエージェント起動時に `startup_mode = "subprocess"` 設定に従い uvicorn サブプロセスとして自動起動する。エージェント起動後に `/mcp status` で各サーバの起動状態を確認できる。

---

## Related Documents

- `01_overview.md`
- `02_deployment.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization

# DB初期化・失敗モード

## 3. DB 初期化

### 3.0 Platform DB overview

The agent uses four SQLite databases. Three have explicit path keys in
`agent.toml`; `workflow_db_path` has no literal entry there and falls back to
`DbConfig`'s Python-level default (`scripts/db/config.py`).

| DB | Default path | Config key | Purpose |
|---|---|---|---|
| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | RAG documents, chunks, embeddings |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | Agent sessions, messages |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` (code default; no `agent.toml` entry) | Task tracking, event processing |
| `eventbus.sqlite` | `/opt/llm/db/eventbus.sqlite` | `eventbus_db_path` | Event Bus records |

Schema details: `90_shared_04_01_db_architecture_and_schema-overview-and-config.md`

### 3.1 スキーマ適用

```bash
bash deploy/init_db.sh
```

**init_db.sh の責務:**
- `workflow.sqlite` と 5つの必須テーブル（tasks, attempts, processed_events, artifacts, approvals）を作成
- インクリメンタルスキーママイグレーションを適用（冪等性あり）
- 全5テーブルが存在することを確認、いずれか欠如時は中止
- スキーマバージョンを記録

### 3.2 デプロイメントチェックリスト

- [ ] `config/workflows/default.json` が存在する
- [ ] `deploy.sh` が正常終了（[FATAL]なし）
- [ ] `init_db.sh` が全5テーブルと正しいスキーマバージョンを報告
- [ ] `setup_services.sh` がプリフライトチェックに合格

### 3.3 失敗モード

| 症状 | 失敗スクリプト | 対処法 |
|---|---|---|
| `[FATAL] Missing required workflow definition` | deploy.sh | config/workflows/default.json を追加 |
| `[FATAL] Workflow definition failed validation; aborting deployment.` | deploy.sh | JSONバリデーションエラーを修正 |
| `[FATAL] Deployed workflow definition checksum does not match source; deployment corrupted.` | deploy.sh | deploy.sh を再実行、ディスク異常を確認 |
| `[FATAL] Workflow database schema is missing or incomplete.` | init_db.sh / setup_services.sh | init_db.sh を再実行 |
| `[FATAL] Workflow schema version mismatch: expected <X>, found <Y>.` | setup_services.sh | init_db.sh でマイグレーション適用 |

For detailed diagnosis and recovery commands per failure mode, see [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook).

For the production `require_approval` category policy (which categories require a post-execution approval gate, and the local-dev exception), see [承認ゲート](05_agent_03_03_turn-processing-flow-workflow-engine.md#承認ゲート).

このデプロイメント要件がなぜ必須なのか(監査・回復・承認状態の永続化という設計判断)については
[ADR-Workflow-Mandatory](05_agent_03_03_turn-processing-flow-workflow-engine.md#ワークフロー実行必須化-adr-workflow-mandatory)を参照。

## Related Documents

- `01_overview.md`
- `02_deployment.md`
- `05_agent_03_03_turn-processing-flow-workflow-engine.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization

### DB Path Reference (auto-generated)

<!-- AUTO-GENERATED: gen_deployment_reference.py db-path-reference -->
Generated from `scripts/db/config.py` and `config/agent.toml`. Do not hand-edit between the guard comments; run `python tools/gen_deployment_reference.py` to refresh.

| DB | Default path | Config key | Set in `agent.toml`? |
|---|---|---|---|
| `eventbus.sqlite` | `/opt/llm/db/eventbus.sqlite` | `eventbus_db_path` | Yes |
| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | Yes |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | Yes |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` | No (Python-level default in `scripts/db/config.py`) |
<!-- END AUTO-GENERATED -->
