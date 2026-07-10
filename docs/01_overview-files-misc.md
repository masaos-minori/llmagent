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
  - 01_overview-files-build.md
  - 01_overview-files-rag.md
  - 01_overview-files-scripts.md
  - 01_overview-files-shared.md
  - 01_overview-files-config.md
  - 01_overview.md
source:
  - 01_overview-files.md
---

# ファイル構成

アーキテクチャ概要 → [`01_overview-arch-process.md`](01_overview-arch-process.md), [`01_overview-arch-pipelines.md`](01_overview-arch-pipelines.md), [`01_overview-arch-features.md`](01_overview-arch-features.md)

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

- `01_overview-files-build.md`
- `01_overview-files-rag.md`
- `01_overview-files-scripts.md`
- `01_overview-files-shared.md`
- `01_overview-files-config.md`

## Keywords

eventbus
logs
deployment
file-structure
system-configuration
