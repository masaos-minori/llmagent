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
- `02_deployment-part2.md`

## Keywords

deployment
environment
setup
installation
llama-cpp
sqlite-vec
db-initialization
