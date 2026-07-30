---
title: "RAG index consistency checks"
category: rag
tags:
  - rag
  - configuration
related:
  - 03_rag_00_document-guide.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_05_1-configuration-reference.md
---

# RAGインデックス整合性チェック

RAGインデックスは、以下の3つのテーブルが同期されている必要がある。
- `chunks` — 正規のチャンクレコード
- `chunks_fts` — FTS5全文検索インデックス (SQLiteトリガーによって生成される)
- `chunks_vec` — ベクトル埋め込みインデックス

## 起動時の警告

エージェント起動ごとに、RAG整合性チェックが`check_rag_consistency()` (COUNTクエリ3件、
読み取り専用、高速) を実行する。不整合が検出された場合、コンソールに警告が出力される。

``` text
[RAG] Consistency issue: fts_gap=3 (3 chunks missing from FTS index)
```

インデックスが健全な場合は警告は表示されない (`logger.info("RAG consistency: OK")`のみが書き込まれる)。

## `/session rag-rebuild-fts` コマンド

`/session rag-rebuild-fts`コマンドは、正規テーブルである`chunks`から`chunks_fts`を再構築する。

**再構築ルール:** 再構築では`COALESCE(normalized_content, content)`をインデックス化する。これはFTS5トリガー (`chunks_ai`) と同一である。

- 日本語チャンク: `normalized_content` (Sudachiで正規化済み) が存在する場合、それがインデックス化される
- 英語/コードチャンク: `normalized_content`はNULLのため、FTS5は直接`content`にフォールバックする
- `chunks_fts`は手動で編集してはならない — これはトリガーまたは再構築処理によって維持される派生インデックスである

**使用場面:**
- `/session rag-consistency`で`fts_gap > 0` (FTSエントリの欠落) が検出された場合
- `fts_orphan_count > 0` (余分なFTSエントリ、データ損失のリスク) の場合
- 大規模な取り込み後にFTSインデックスの整合性を確認する場合

**修復の判断フロー:**

| Issue | Fix |
|---|---|
| `fts_gap > 0` | `/session rag-rebuild-fts`を実行 — FTSエントリが欠落しているため、`chunks`から再構築 |
| `fts_orphan_count > 0` | `/session rag-rebuild-fts`を実行 — FTSに余分なエントリがある (データ損失のリスクあり、緊急対応) |

## `/session rag-consistency` コマンド

`/session rag-consistency`コマンドは数値カウントを表示し、続けてOKまたはエラーの概要を表示する。

``` yaml
  chunks: 1042  fts: 1042  vec: 1042  fts_gap: 0  orphan_vec: 0  fts_orphan: 0
RAG consistency: OK (chunks/FTS/vec in sync)
```

不整合がある場合:

``` yaml
  chunks: 1042  fts: 1039  vec: 1042  fts_gap: 3  orphan_vec: 0  fts_orphan: 0
RAG consistency: FAIL
Consistency issue: [WARNING] FTS gap detected (chunks=1042, fts=1039, gap=3). Affected doc_ids: [1, 2, 3]. Run '/session rag-rebuild-fts' to repair.
```

## 閾値の方針

このチェックは**厳格なゼロ**閾値を使用する。すなわち、`fts_gap`、`fts_orphan_count`、
`orphan_vec_count`のいずれかが0以外であれば不整合として報告される。設定可能な閾値
(例: `fts_gap <= 5`を許容する) は実装されていない。部分的なOK判定の方針が必要かどうかは**確認が必要**。

## 不整合の修正

`/session rag-consistency`を使用して問題を検出する。レポートには影響を受けた`chunk_id`/URLの
識別子 (それぞれ最大10件) が含まれるため、運用者は手動でDBを調査せずに対応できる。

**修復の判断フロー:**

| Issue | Fix |
|---|---|
| `fts_gap > 0` | `/session rag-rebuild-fts`を実行 — FTSエントリが欠落しているため、`chunks`から再構築 |
| `fts_orphan_count > 0` | `/session rag-rebuild-fts`を実行 — FTSに余分なエントリがある (データ損失のリスクあり、緊急対応) |
| `orphan_vec_count > 0` | 該当URLに対して`ingester.py --force`を実行 — `chunks`に対応する行がない`chunks_vec`の行 |
| `vec != chunks` | 該当URLに対して`ingester.py --force`を実行 — 埋め込みステップが失敗した可能性が高い |

`/session rag-rebuild-fts`を実行して、`chunks`テーブルから`chunks_fts`を再同期する。


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
