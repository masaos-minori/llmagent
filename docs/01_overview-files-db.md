---
title: "ファイル構成（データベース層）"
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

├─ db/
│   ├─ rag.sqlite                     # RAG ベクトル DB (documents/chunks/chunks_vec/chunks_fts) — see 90_shared_04 §3-§6
│   ├─ session.sqlite                 # エージェントセッション + メッセージ — see 90_shared_04 §2
│   └─ workflow.sqlite                # タスク追跡 + イベント処理 — see 90_shared_04 §7
├─ sqlite-vec/
│   └─ vec0.so                        # SQLite ベクトル検索拡張 (ロード可能拡張モジュール)
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
