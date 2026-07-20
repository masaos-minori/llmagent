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
  - 01_overview-files-01-build.md
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
├─ rag-src/                           # クロール済みテキスト (yyyymmddhhmmss-{slug}.json)
│   ├─ chunk/                         # チャンク分割済みファイル ({stem}-{idx:04d}.json)
│   └─ registered/                    # DB 投入済みファイル (ingester.py が移動)
├─ sqlite-vec/
│   └─ vec0.so                        # SQLite ベクトル検索拡張 (ロード可能拡張モジュール)
```

## Related Documents

- `01_overview-files-01-build.md`
- `01_overview-files-03-scripts-part1.md`
- `01_overview-files-04-shared-part1.md`
- `01_overview-files-05-config.md`
- `01_overview-files-06-misc.md`

## Keywords

rag
rag-src
crawler
chunk-splitter
ingester
embedding
file-structure
