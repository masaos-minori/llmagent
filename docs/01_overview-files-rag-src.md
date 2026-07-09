---
title: "ファイル構成（RAG取込データ）"
category: overview
tags:
  - overview
  - file-structure
related:
  - 01_overview.md
  - 01_overview-arch-process.md
source:
  - 01_overview-files.md
---

├─ rag-src/                           # クロール済みテキスト (yyyymmddhhmmss-{slug}.json)
│   ├─ chunk/                         # チャンク分割済みファイル ({stem}-{idx:04d}.json)
│   └─ registered/                    # DB 投入済みファイル (ingester.py が移動)
├─ db/
│   ├─ rag.sqlite                     # RAG ベクトル DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 §3-§6
│   ├─ session.sqlite                 # エージェントセッション + メッセージ — see 90_shared_04 §2
│   └─ workflow.sqlite                # タスク追跡 + イベント処理 — see 90_shared_04 §7
## Related Documents

- `01_overview.md`
- `01_overview-arch-process.md`

## Keywords

file-structure
directory
layout
configuration
scripts
shared
database
event-bus
