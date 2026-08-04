---
title: "Miscellaneous File Structure"
category: overview
tags:
  - eventbus
  - logs
  - deployment
  - file-structure
  - system-configuration
related:
  - 01_overview-files-01-build.md
  - 01_overview-files-02-rag.md
  - 01_overview-files-03-scripts-part1.md
  - 01_overview-files-04-shared-part1.md
  - 01_overview-files-05-config.md
---

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:

``` text
/opt/llm/
├─ scripts/
│   └─ eventbus/                        # イベントバスパッケージ
│       ├─ app.py                       # FastAPI アプリケーション
│       ├─ broker.py                    # メッセージブローカー
│       ├─ config.py                    # イベントバス設定
│       ├─ db.py                        # データベースアクセス層
│       ├─ offsets.py                   # オフセット管理
│       ├─ dlq.py                       # DLQ (Dead Letter Queue)
│       ├─ publish_route.py             # publish エンドポイント
│       ├─ subscribe_route.py           # subscribe エンドポイント
│       ├─ ack_route.py                 # ack エンドポイント
│       ├─ dlq_route.py                 # DLQ エンドポイント
│       ├─ replay_route.py              # リプレイエンドポイント
│       ├─ health_route.py              # ヘルスチェックエントポイント
│       ├─ route_helpers.py             # ルートハンドラ共通ヘルパー
│       ├─ schema.sql                   # イベントバスDBスキーマ
│       └─ __init__.py                  # イベントバスパッケージ初期化
```

イベントの配信失敗とリカバリフロー：
メッセージの受信拒否（nack）が発生すると、`ack_route.py` を介して `db.py` の `delivery_failure_count` がインクリメントされます。このカウントが `max_retry` に達したイベントは、`dlq.py` によって `dlq_at` タイムスタンプが付与され、DLQ (Dead Letter Queue) へ昇格されます。DLQ の確認および復旧は `dlq_route.py` を通じて行われ、`dlq_list` による一覧取得や `dlq_requeue` によるアクティブキューへの再投入が可能です。なお、`offsets.py` と `replay_route.py` によるリプレイ機能は、コンシューマーのキャッチアップ（過去のオフセットからの再読み込み）のための独立した仕組みであり、DLQ からの復旧とは別のプロセスです。


リポジトリルート:
``` text
conf.d/
├─ cicd-mcp                             # GITHUB_TOKEN (Personal Access Token) 設定
├─ git-mcp                              # allowed_repo_paths (fail-closed) / read_only 設定
├─ github-mcp                           # GITHUB_TOKEN (Personal Access Token) 設定
└─ web-search-mcp                       # 各検索プロバイダのAPIキー設定 (優先順位はweb_search_mcp_server.jsonで指定)
```

## Related Documents

- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-04-shared-part1.md`
- `01_overview-files-05-config.md`
- [01_overview.md](01_overview.md)

## Keywords

eventbus
logs
deployment
file-structure
system-configuration
