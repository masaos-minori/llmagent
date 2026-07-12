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
  - 01_overview-files-05-config.md
  - 01_overview.md
---

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-01-process.md`](01_overview-arch-01-process.md), [`01_overview-arch-02-pipelines.md`](01_overview-arch-02-pipelines.md), [`01_overview-arch-03-features.md`](01_overview-arch-03-features.md)

## 3. ファイル構成

デプロイ先のディレクトリ構成:

```
/opt/llm/
├─ eventbus/                            # イベントバスパッケージ
│   ├─ app.py                           # FastAPI アプリケーション
│   ├─ broker.py                        # メッセージブローカー
│   ├─ config.py                        # イベントバス設定
│   ├─ db.py                            # データベースアクセス層
│   ├─ offsets.py                       # オフセット管理
│   ├─ dlq.py                           # DLQ (Dead Letter Queue)
│   ├─ publish_route.py                 # publish エンドポイント
│   ├─ subscribe_route.py               # subscribe エンドポイント
│   ├─ ack_route.py                     # ack エンドポイント
│   ├─ dlq_route.py                     # DLQ エンドポイント
│   ├─ replay_route.py                  # リプレイエンドポイント
│   ├─ health_route.py                  # ヘルスチェックエントポイント
│   ├─ schema.sql                       # イベントバスDBスキーマ
│   └─ __init__.py                      # イベントバスパッケージ初期化
    └─ logs/                                    # 各サービスのログファイル出力先
/etc/conf.d/
   └─ github-mcp                         # GITHUB_TOKEN (Personal Access Token) 設定
```

## Related Documents

- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts.md`
- `01_overview-files-04-shared.md`
- `01_overview-files-05-config.md`

## Keywords

eventbus
logs
deployment
file-structure
system-configuration
