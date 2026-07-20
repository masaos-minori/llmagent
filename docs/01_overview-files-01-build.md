---
title: "Build and Models File Structure"
category: overview
tags:
  - build
  - llama-cpp
  - models
  - gguf
  - deployment
  - file-structure
related:
  - 01_overview-files-02-rag.md
  - 01_overview-files-05-config.md
  - 01_overview-files-06-misc.md
  - 01_overview.md
---

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:

``` text
/opt/llm/
├─ llama.cpp/                                 # llama.cpp ソース・ビルド成果物
├─ models/
│   ├─ Qwen3.6-Instruct-Q4_K_M.gguf           # チャット/コード生成用 LLM (MQE・再ランク兼用, :8080)
│   └─ multilingual-E5-small.gguf             # 埋込用 LLM (384 次元, :8081)
```

デプロイスクリプト (リポジトリ `deploy/` 配下、`bash deploy/xxx.sh` で実行):

``` text
deploy/
├─ deploy.sh                                  # Python スクリプト・設定・SQL を /opt/llm/ へコピー
├─ build_sqlite_vec.sh                        # sqlite-vec (vec0.so) を取得・ビルド。初回デプロイ時に一度実行
├─ init_db.sh                                 # SQLite スキーマ初期化。deploy.sh 実行後に一度だけ実行
├─ setup_services.sh                          # MCP サーバ (:8004-:8014) と LLM サーバ (:8080-:8081) を
│                                              # エージェント管理 subprocess として起動
└─ start_agent.sh                             # AgentREPL を起動 (production では /opt/llm/pyproject.toml を優先)
```

### 実装上の補足 (Current behavior)

- `deploy.sh` と `setup_services.sh` はいずれも `config/workflows/default.json` の存在チェックと
  `python -m agent.workflow.validate` によるスキーマ検証を必須の前提条件としており、検証に失敗すると
  `[FATAL]` を出力してデプロイ/起動を中断する (exit 1)。ワークフロー定義なしでの運用は想定されていない。
  (根拠分類: Explicit in code — `deploy/deploy.sh`, `deploy/setup_services.sh`)
- `setup_services.sh` はさらに `/opt/llm/db/workflow.sqlite` の存在と `tasks/attempts/processed_events/artifacts/approvals`
  テーブルの有無を確認する。欠落時も `[FATAL]` で中断する。
  (根拠分類: Explicit in code — `deploy/setup_services.sh`)

## Related Documents

- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-04-shared-part1.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`

## Keywords

build
llama-cpp
models
gguf
deployment
file-structure
