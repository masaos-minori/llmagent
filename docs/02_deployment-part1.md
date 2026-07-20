---
title: "Deployment Guide (Part 1)"
category: deployment
tags:
  - deployment
  - environment
  - setup
related:
  - 01_overview.md
source:
  - 02_deployment-part1.md
---

# 導入手順・デプロイ

## Embedding: multilingual-E5-small (384 dim)

### 1.1 Gentoo Linux パッケージ導入

```bash
emerge --ask sys-devel/gcc sys-devel/make dev-util/cmake dev-util/ninja

emerge --ask dev-db/sqlite

sqlite3 :memory: "CREATE VIRTUAL TABLE t USING fts5(x); INSERT INTO t VALUES('テスト'); SELECT * FROM t WHERE t MATCH 'テスト';"

emerge --ask dev-lang/python:3.13

emerge --ask dev-libs/libxml2 dev-libs/libxslt

emerge --ask dev-vcs/git
```

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

`/opt/llm/venv/requirements.txt`:

``` text
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

uv run --with huggingface-hub huggingface-cli download ggml-org/multilingual-e5-small-Q8_0-GGUF \
    multilingual-e5-small-Q8_0.gguf \
    --local-dir /opt/llm/models/
mv /opt/llm/models/multilingual-e5-small-Q8_0.gguf \
   /opt/llm/models/multilingual-E5-small.gguf

uv run --with huggingface-hub huggingface-cli download bartowski/gemma-4-e4b-it-GGUF \
    gemma-4-e4b-it-Q4_K_M.gguf \
    --local-dir /opt/llm/models/

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
bash deploy/setup_services.sh

curl -s http://127.0.0.1:8081/health   # embed-llm
curl -s http://127.0.0.1:8080/health   # agent-llm

bash deploy/start_agent.sh
```

### 実装上の補足(起動方法)

`deploy/start_agent.sh` は `/opt/llm/pyproject.toml` の有無で本番(`/opt/llm`)/開発(リポジトリルート)を自動判別し、当該ルートで `python -m agent` (`scripts/agent/__main__.py`)を実行する。(Explicit in code)

> API キーの設定:
> - Web 検索: DuckDuckGo — API キー不要
> - GitHub 操作: `GITHUB_TOKEN` を `conf.d/github-mcp` に設定

### 2.4 MCP サーバの確認

MCP サーバはエージェント起動時に `startup_mode = "subprocess"` 設定に従い uvicorn サブプロセスとして自動起動する。エージェント起動後に `/mcp status` で各サーバの起動状態を確認できる。

---

## Related Documents

- `01_overview.md`
- `02_deployment-part2.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization
