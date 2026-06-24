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

# 埋込用: multilingual-E5-small (384 次元)
# E5 モデルのプレフィックス: 取込時 "passage: "、クエリ時 "query: "
uv run --with huggingface-hub huggingface-cli download ggml-org/multilingual-e5-small-Q8_0-GGUF \
    multilingual-e5-small-Q8_0.gguf \
    --local-dir /opt/llm/models/
mv /opt/llm/models/multilingual-e5-small-Q8_0.gguf \
   /opt/llm/models/multilingual-E5-small.gguf

# チャット用: gemma-4-e4b (Gemma 4 4B パラメータ instruction-tuned)
uv run --with huggingface-hub huggingface-cli download bartowski/gemma-4-e4b-it-GGUF \
    gemma-4-e4b-it-Q4_K_M.gguf \
    --local-dir /opt/llm/models/

# コード生成用: Qwen2.5-Coder-7B
uv run --with huggingface-hub huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct-GGUF \
    Qwen3.6-Instruct-Q4_K_M.gguf \
    --local-dir /opt/llm/models/

ls -lh /opt/llm/models/
```

---

## 2. サービス設定

### 2.1 sqlite-vec のビルド (初回のみ)

SQLite のベクトル近傍探索 (KNN: K-Nearest Neighbor) 拡張。`vec0` 仮想テーブルを通じてベクトル埋込の保存と類似度検索を提供。

```bash
bash deploy/build_sqlite_vec.sh
```

インストール先: `/opt/llm/sqlite-vec/vec0.so` (`common.toml` の `sqlite_vec_so` と一致)

### 2.2 スクリプトのデプロイ

`deploy/deploy.sh` がスクリプト・設定ファイル・SQL ファイルの一括コピーを実行。

```bash
# リポジトリのルートから実行する
bash deploy/deploy.sh
```

deploy.sh が行う処理:
- `/opt/llm/scripts/` に Python スクリプトをコピー (`eventbus/` パッケージを含む)
- `/opt/llm/config/` に設定ファイルをコピー (`eventbus.toml` を含む)
- `/opt/llm/schemas/` に JSON Schema をコピー (`event_envelope.json` を含む)
- `/opt/llm/logs/`, `/opt/llm/rag-src/chunk/`, `/opt/llm/rag-src/registered/` を作成
- `/opt/llm/storage/`, `/opt/llm/offsets/`, `/opt/llm/deadletter/` を作成 (Event Bus 用)

### 2.3 LLM サービス登録・起動

`deploy/setup_services.sh` が LLM サービスの初期化を実行。

MCP サーバ (ports 8004-8014) はエージェント起動時に agent-managed subprocess として自動起動する。

```bash
# deploy.sh 実行後に実行する
bash deploy/setup_services.sh

# ヘルスチェック (各 LLM サービスがモデルロードを完了するまで待機)
curl -s http://127.0.0.1:8003/health   # embed-llm
curl -s http://127.0.0.1:8001/health   # agent-llm

# LLM サービスのモデルロード完了後にエージェントを起動する
/opt/llm/scripts/agent.py
```

> API キーの設定:
> - Web 検索: DuckDuckGo — API キー不要
> - GitHub 操作: `GITHUB_TOKEN` を `/etc/conf.d/github-mcp` に設定

### 2.4 MCP サーバの確認

MCP サーバはエージェント起動時に `startup_mode = "subprocess"` 設定に従い uvicorn サブプロセスとして自動起動する。エージェント起動後に `/mcp status` で各サーバの起動状態を確認できる。

```bash
# エージェント内で確認
agent[chat]> /mcp status
```

---

## 3. DB 初期化

### 3.0 プラットフォーム DB 概要

エージェントは 3 つの SQLite データベースを使用する。すべてのパスは `common.toml` で設定する。

| DB | デフォルトパス | 設定キー | 用途 |
|---|---|---|---|
| `rag.sqlite` | `/opt/llm/db/rag.sqlite` | `rag_db_path` | RAG ドキュメント・チャンク・埋込 |
| `session.sqlite` | `/opt/llm/db/session.sqlite` | `session_db_path` | エージェントセッション・メッセージ |
| `workflow.sqlite` | `/opt/llm/db/workflow.sqlite` | `workflow_db_path` | タスク追跡・イベント処理 |

スキーマ詳細: `90_shared_04_db_architecture_and_schema.md`

### 3.1 スキーマ適用

```bash
# deploy/deploy.sh 実行済みであること (スクリプトと設定ファイルが配置されていること)
bash deploy/init_db.sh
# 出力: Schema created successfully.
# テーブル確認 (chunks  chunks_fts  chunks_vec  documents)
```

### 3.2 スキーマ概要

| テーブル | 種別 | 主な列 | 用途 |
|---|---|---|---|
| `documents` | 通常 | `doc_id` PK, `url` UNIQUE, `lang` | URL 単位のドキュメント管理 |
| `chunks` | 通常 | `chunk_id` PK, `doc_id` FK, `content` | 分割チャンク本文 |
| `chunks_fts` | FTS5 仮想 | `content`, `content_rowid='chunk_id'` | BM25 全文検索 |
| `chunks_vec` | vec0 仮想 | `chunk_id` PK, `embedding float[384]` | KNN ベクトル検索 |
| `sessions` | 通常 | `session_id` PK, `created_at`, `title` | REPL セッション管理 |
| `messages` | 通常 | `message_id` PK, `session_id` FK, `role`, `content`, `tool_calls` | 会話メッセージの永続化 |

FTS5 は `chunks` テーブルの INSERT/UPDATE/DELETE に対してトリガーで自動同期 (`chunks_ai` / `chunks_au` / `chunks_ad`)。

`sessions` と `messages` は REPL エージェント (`agent.py`) が使用する会話履歴の永続化テーブル。`/session list` で一覧表示、`/session load <id>` で過去セッションの文脈を復元可能。

