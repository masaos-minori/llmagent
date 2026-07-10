---
title: "RAG Files File Structure"
category: overview
tags:
  - rag
  - rag-src
  - crawler
  - chunk-splitter
  - ingester
  - embedding
  - file-structure
related:
  - 01_overview-files-build.md
  - 01_overview-files-scripts.md
  - 01_overview-files-shared.md
  - 01_overview-files-config.md
  - 01_overview-files-misc.md
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
├─ rag-src/                           # クロール済みテキスト (yyyymmddhhmmss-{slug}.json)
│   ├─ chunk/                         # チャンク分割済みファイル ({stem}-{idx:04d}.json)
│   └─ registered/                    # DB 投入済みファイル (ingester.py が移動)
├─ sqlite-vec/
│   └─ vec0.so                        # SQLite ベクトル検索拡張 (ロード可能拡張モジュール)
```

## Related Documents

- `01_overview-files-build.md`
- `01_overview-files-scripts.md`
- `01_overview-files-shared.md`
- `01_overview-files-config.md`
- `01_overview-files-misc.md`

## Keywords

rag
rag-src
crawler
chunk-splitter
ingester
embedding
file-structure
