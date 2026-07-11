---
title: "Deployment Guide"
category: deployment
tags:
  - deployment
  - environment
  - setup
related:
  - 01_overview.md
source:
  - 02_deployment.md
---

# 導入手順・デプロイ

## 1. 事前準備

### 1.1 Gentoo Linux パッケージ導入

```bash
# ビルドツール
emerge --ask sys-devel/gcc sys-devel/make dev-util/cmake dev-util/ninja

# SQLite (FTS5 有効、Gentoo の dev-db/sqlite は標準で FTS5 を含む)
emerge --ask dev-db/sqlite

# FTS5 動作確認
sqlite3 :memory: "CREATE VIRTUAL TABLE t USING fts5(x); INSERT INTO t VALUES('テスト'); SELECT * FROM t WHERE t MATCH 'テスト';"

# Python 3.13 以上
emerge --ask dev-lang/python:3.13

# BeautifulSoup4 の lxml パーサ用ライブラリ
emerge --ask dev-libs/libxml2 dev-libs/libxslt

# git (sqlite-vec・llama.cpp ソース取得用)
emerge --ask dev-vcs/git
```

> Python の `sqlite3` モジュールがロード拡張に対応していない場合:
> ```bash
> echo 'dev-lang/python sqlite' >> /etc/portage/package.use/python
> emerge --ask dev-lang/python
> ```

### 1.2 Python 環境構築 (uv を使用)

```bash
# uv をインストール (https://docs.astral.sh/uv/)
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトの依存関係をインストール
uv sync --dev --system-certs
```

`/opt/llm/venv/requirements.txt`:

```
fastapi>=0.111.0
uvicorn[standard]>=0.30.0
httpx>=0.27.0
pydantic>=2.7.0
requests>=2.32.0
beautifulsoup4>=4.12.0
lxml>=5.0.0
trafilatura>=1.12.0
langdetect>=1.0.9
sudachipy>=0.6.8
sudachidict-core
huggingface-hub>=0.23.0
duckduckgo-search>=6.0.0
PyGithub>=2.3.0
```

```bash
# 依存関係をインストール
uv pip install -r /opt/llm/venv/requirements.txt
```

### 1.3 llama.cpp のビルド

GGUF (GPT-Generated Unified Format) 形式のモデルを CPU で動作させる推論エンジン。

```bash
git clone https://github.com/ggerganov/llama.cpp.git /opt/llm/llama.cpp
cd /opt/llm/llama.cpp

cmake -B build \
    -DGGML_NATIVE=ON \
    -DLLAMA_SERVER=ON \
    -DCMAKE_BUILD_TYPE=Release

cmake --build build --config Release -j$(nproc)
/opt/llm/llama.cpp/build/bin/llama-server --version
```

### 1.4 LLM モデルの取得

```bash
mkdir -p /opt/llm/models

# Embedding: multilingual-E5-small (384 dim)
# E5 model prefix: "passage: " for ingestion, "query: " for queries
uv run --with huggingface-hub huggingface-cli download ggml-org/multilingual-e5-small-Q8_0-GGUF \
    multilingual-e5-small-Q8_0.gguf \
    --local-dir /opt/llm/models/
mv /opt/llm/models/multilingual-e5-small-Q8_0.gguf \
   /opt/llm/models/multilingual-E5-small.gguf

# LLM: gemma-4-e4b (Gemma 4 4B parameter instruction-tuned)
uv run --with huggingface-hub huggingface-cli download bartowski/gemma-4-e4b-it-GGUF \
    gemma-4-e4b-it-Q4_K_M.gguf \
    --local-dir /opt/llm/models/

# LLM: Qwen2.5-Coder-7B
uv run --with huggingface-hub huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF \
    Qwen3.6-Instruct-Q4_K_M.gguf \
    --local-dir /opt/llm/models/

ls -lh /opt/llm/models/
```

---

## 2. サービス設定

### 2.1 Building sqlite-vec (first time only)

SQLite vector approximate nearest neighbor (KNN: K-Nearest Neighbor) extension. Provides vector embedding storage and similarity search via the `vec0` virtual table.

```bash
bash deploy/build_sqlite_vec.sh
```

Install path: `/opt/llm/sqlite-vec/vec0.so` (must match `sqlite_vec_so` in `agent.toml`)

### 2.2 Deploying scripts

`deploy/deploy.sh` performs bulk copying of scripts, config files, and SQL files.

```bash
# Execute from the repository root
bash deploy/deploy.sh
```

deploy.sh does:
- Copies Python scripts to `/opt/llm/scripts/` (includes `eventbus/` package)
- Copies config files to `/opt/llm/config/` (includes `eventbus.toml`)
- Copies JSON Schema to `/opt/llm/schemas/` (includes `event_envelope.json`)
- Creates `/opt/llm/logs/`, `/opt/llm/rag-src/chunk/`, `/opt/llm/rag-src/registered/`
- Creates `/opt/llm/storage/`, `/opt/llm/offsets/`, `/opt/llm/deadletter/` (Event Bus)

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
# deploy.sh 実行後に実行する
bash deploy/setup_services.sh

# Health check (wait for each LLM service to complete model loading)
curl -s http://127.0.0.1:8003/health   # embed-llm
curl -s http://127.0.0.1:8001/health   # agent-llm

# Start the agent after LLM services complete model loading
/opt/llm/scripts/agent.py
```

> API キーの設定:
> - Web 検索: DuckDuckGo — API キー不要
> - GitHub 操作: `GITHUB_TOKEN` を `/etc/conf.d/github-mcp` に設定

### 2.4 MCP サーバの確認

MCP サーバはエージェント起動時に `startup_mode = "subprocess"` 設定に従い uvicorn サブプロセスとして自動起動する。エージェント起動後に `/mcp status` で各サーバの起動状態を確認できる。

---

## 3. DB 初期化

### 3.0 Platform DB overview

The agent uses three SQLite databases. All paths are configured in `agent.toml`.

| DB | Default path | Config key | Purpose |

| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | RAG documents, chunks, embeddings |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | Agent sessions, messages |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` | Task tracking, event processing |

Schema details: `90_shared_04_db_overview_and_config.md`

### 3.1 Applying schema

```bash
# Ensure deploy/deploy.sh has been run (scripts and config files are in place)
bash deploy/init_db.sh
# Output: Schema created successfully.
# Verify tables (chunks  chunks_fts  chunks_vec  documents)
```

**Workflow schema responsibilities (init_db.sh):**
- Creates `workflow.sqlite` and its required tables (`tasks`, `attempts`, `processed_events`, `artifacts`, `approvals`) via `create_workflow_schema()`
- Applies incremental schema migrations (idempotent — safe to re-run)
- Verifies all 5 required tables exist after initialization; aborts if any are missing
- Records the current workflow schema version in `workflow_schema_version`

### 3.2 Workflow deployment checklist

- [ ] `config/workflows/default.json` exists in the repository before running `deploy.sh`
- [ ] `bash deploy/deploy.sh` completes with a printed workflow Name/Version/Stages/SHA256 block and no `[FATAL]` errors
- [ ] `bash deploy/init_db.sh` reports all 5 workflow tables present and the expected schema version recorded
- [ ] `bash deploy/setup_services.sh` passes its pre-flight workflow checks before any service starts

### 3.3 Workflow deployment failure modes

| Symptom | Failing script | Remediation |
|---|---|---|
| `[FATAL] Missing required workflow definition` | `deploy.sh` | Add `config/workflows/default.json` to the repository before deploying |
| `[FATAL] Invalid workflow definition ...` | `deploy.sh` | Fix the JSON per the printed validation error (missing field, duplicate stage ID, invalid retry policy, etc.) |
| `[FATAL] Deployed workflow definition checksum does not match source` | `deploy.sh` | Re-run `deploy.sh`; investigate why the copy was not byte-identical (disk/filesystem issue) |
| `[FATAL] Workflow database schema is missing or incomplete` | `init_db.sh` or `setup_services.sh` | Run `bash deploy/init_db.sh` to (re-)create the workflow schema |
| `[FATAL] Workflow schema version mismatch` | `setup_services.sh` (or `RuntimeError` at agent startup) | Run `bash deploy/init_db.sh` to apply pending migrations and record the current version |

For detailed diagnosis and recovery commands per failure mode, see [Workflow Deployment Runbook](05_agent_10_04_operations-and-observability-validation-and-troubleshooting.md#workflow-deployment-runbook).

## Related Documents

- `01_overview.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization

