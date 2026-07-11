---
title: "System Overview Index"
category: overview
tags:
  - system-overview
  - architecture
  - introduction
  - index
related:
  - 01_overview-arch-01-process.md
  - 01_overview-arch-02-pipelines.md
  - 01_overview-arch-03-features.md
  - 01_overview-files-01-build.md
  - 01_overview-files-02-rag.md
  - 01_overview-files-03-scripts-part1.md
  - 01_overview-files-04-shared-part1.md
  - 01_overview-files-05-config.md
  - 01_overview-files-06-misc.md
source:
  - 01_overview.md
---

# 概要・アーキテクチャ・ファイル構成(索引)

| ファイル | 内容 |
|---|---|
| [01_overview-arch-01-process.md](01_overview-arch-01-process.md) | プロセスアーキテクチャ(LLMサービス、MCPサーバ、設定分離) |
| [01_overview-arch-02-pipelines.md](01_overview-arch-02-pipelines.md) | パイプラインアーキテクチャ(取込/検索パイプライン、ターン処理順序、ワークフローモード) |
| [01_overview-arch-03-features.md](01_overview-arch-03-features.md) | 機能アーキテクチャ(実装済み機能、実装上の補足) |
| [01_overview-files-01-build.md](01_overview-files-01-build.md) | ビルド・モデル関連のファイル構成 |
| [01_overview-files-02-rag.md](01_overview-files-02-rag.md) | RAG関連のファイル構成 |
| [01_overview-files-03-scripts-part1.md](01_overview-files-03-scripts-part1.md) 〜 part5 | scripts配下のファイル構成(5分割) |
| [01_overview-files-04-shared-part1.md](01_overview-files-04-shared-part1.md) 〜 part2 | 共有インフラのファイル構成(2分割) |
| [01_overview-files-05-config.md](01_overview-files-05-config.md) | 設定ファイル構成 |
| [01_overview-files-06-misc.md](01_overview-files-06-misc.md) | その他のファイル構成 |

## 実装意図

- `01_overview-arch.md` をH2境界で3ファイルに分割: process, pipelines, features
- `01_overview-files.md` をディレクトリ単位の論理境界で6ファイルに分割: build, rag, scripts, shared, config, misc
- 各ファイルにtitle/category/tags/related documents/keywordsを含むYAML Front Matterを付与
- 本ファイルはシステム全体の概要索引。各詳細ドキュメントセットは以下のカタログを参照

## 他のドキュメントセット

| ファイル | 内容 |
|---|---|
| [02_deployment-part1.md](02_deployment-part1.md) | 導入手順・デプロイ |
| [03_rag_00_document-guide.md](03_rag_00_document-guide.md) | RAGドキュメントセットガイド(全ファイル一覧) |
| [04_mcp_00_document-guide.md](04_mcp_00_document-guide.md) | MCPドキュメントセットガイド(全ファイル一覧) |
| [05_agent_00_document-guide.md](05_agent_00_document-guide.md) | Agentドキュメントセットガイド(全ファイル一覧) |
| [90_shared_00_document-guide.md](90_shared_00_document-guide.md) | shared/DBドキュメントセットガイド(全ファイル一覧) |

## Related Documents

- `01_overview-arch-01-process.md`
- `01_overview-arch-02-pipelines.md`
- `01_overview-arch-03-features.md`
- `01_overview-files-01-build.md`
- `01_overview-files-02-rag.md`
- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-04-shared-part1.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`
- `02_deployment-part1.md`

## Keywords

system-overview
architecture
introduction
index
overview
deployment
rag
mcp
agent
shared
