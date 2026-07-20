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

### 起動時の警告

エージェント起動ごとに、RAG整合性チェックが`check_rag_consistency()` (COUNTクエリ3件、
読み取り専用、高速) を実行する。不整合が検出された場合、コンソールに警告が出力される。

```
[RAG] Consistency issue: fts_gap=3 (3 chunks missing from FTS index)
```

インデックスが健全な場合は警告は表示されない (`logger.info("RAG consistency: OK")`のみが書き込まれる)。

### `/db rag rebuild-fts` コマンド

`/db rag rebuild-fts`コマンドは、正規テーブルである`chunks`から`chunks_fts`を再構築する。

**再構築ルール:** 再構築では`COALESCE(normalized_content, content)`をインデックス化する。これはFTS5トリガー (`chunks_ai`) と同一である。

- 日本語チャンク: `normalized_content` (Sudachiで正規化済み) が存在する場合、それがインデックス化される
- 英語/コードチャンク: `normalized_content`はNULLのため、FTS5は直接`content`にフォールバックする
- `chunks_fts`は手動で編集してはならない — これはトリガーまたは再構築処理によって維持される派生インデックスである

**使用場面:**
- `/db consistency`で`fts_gap > 0` (FTSエントリの欠落) が検出された場合
- `fts_orphan_count > 0` (余分なFTSエントリ、データ損失のリスク) の場合
- 大規模な取り込み後にFTSインデックスの整合性を確認する場合

**修復の判断フロー:**

| Issue | Fix |
|---|---|
| `fts_gap > 0` | `/db rag rebuild-fts`を実行 — FTSエントリが欠落しているため、`chunks`から再構築 |
| `fts_orphan_count > 0` | `/db rag rebuild-fts`を実行 — FTSに余分なエントリがある (データ損失のリスクあり、緊急対応) |

### `/db consistency` コマンド

`/db consistency`コマンドは数値カウントを表示し、続けてOKまたはエラーの概要を表示する。

```
  chunks: 1042  fts: 1042  vec: 1042  fts_gap: 0  orphan_vec: 0  fts_orphan: 0
RAG consistency: OK (chunks/FTS/vec in sync)
```

不整合がある場合:

```
  chunks: 1042  fts: 1039  vec: 1042  fts_gap: 3  orphan_vec: 0  fts_orphan: 0
RAG consistency: FAIL
Consistency issue: [WARNING] FTS gap detected (chunks=1042, fts=1039, gap=3). Affected doc_ids: [1, 2, 3]. Run '/db rag rebuild-fts' to repair.
```

### 閾値の方針

このチェックは**厳格なゼロ**閾値を使用する。すなわち、`fts_gap`、`fts_orphan_count`、
`orphan_vec_count`のいずれかが0以外であれば不整合として報告される。設定可能な閾値
(例: `fts_gap <= 5`を許容する) は実装されていない。部分的なOK判定の方針が必要かどうかは**確認が必要**。

### 不整合の修正

`/db consistency`を使用して問題を検出する。レポートには影響を受けた`chunk_id`/URLの
識別子 (それぞれ最大10件) が含まれるため、運用者は手動でDBを調査せずに対応できる。

**修復の判断フロー:**

| Issue | Fix |
|---|---|
| `fts_gap > 0` | `/db rag rebuild-fts`を実行 — FTSエントリが欠落しているため、`chunks`から再構築 |
| `fts_orphan_count > 0` | `/db rag rebuild-fts`を実行 — FTSに余分なエントリがある (データ損失のリスクあり、緊急対応) |
| `orphan_vec_count > 0` | 該当URLに対して`ingester.py --force`を実行 — `chunks`に対応する行がない`chunks_vec`の行 |
| `vec != chunks` | 該当URLに対して`ingester.py --force`を実行 — 埋め込みステップが失敗した可能性が高い |

`/db rag rebuild-fts`を実行して、`chunks`テーブルから`chunks_fts`を再同期する。


<!-- AUTO-GENERATED: gen_rag_reference.py config -->

### 実装上の補足(このAUTO-GENERATEDブロックについて)

`tools/gen_rag_reference.py` の出力先は `docs/03_rag_05_configuration_and_operations.md` (`OPS_DOC`定数) だが、ドキュメント分割後の現構成にはこのファイルは存在しないため、本ブロックはツールによる自動更新の対象外になっている。値は [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md) の方が最新かつ正本であり、以下は現在の設定ファイルに合わせて手動修正済み。(Explicit in code / Needs confirmation — ツールのOPS_DOC定数を分割後のファイルに追随させる方針は未確認)

| Key | Default | Description |
|---|---|---|
| `rag_src_dir` | `/opt/llm/rag-src` | — |
| `crawl_delay` | `1.5` | — |
| `max_depth` | `3` | — |
| `min_chunk` | `40` | — |
| `max_chunk` | `500` | — |
| `embed_retry` | `3` | — |
| `embed_workers` | `4` | — |
| `fetch_retry` | `3` | — |
| `fetch_timeout` | `15` | — |
| `crawl_concurrency` | `3` | — |
| `max_pages` | `200` | — |
| `chunk_overlap` | `50` | — |
| `md_index_enable` | `False` | — |
| `md_snippet_max_chars` | `600` | — |
| `skip_nofollow` | `True` | — |
| `skip_external` | `True` | — |
| `target_urls` | `[['https://ziglang.org/documentation/master/', 'en'], ['https://zig.guide/', 'en'], ['https://www.ruby-lang.org/en/documentation/quickstart/', 'en'], ['https://www.ruby-lang.org/ja/documentation/quickstart/', 'ja'], ['https://docs.ruby-lang.org/en/3.4/doc/', 'en'], ['https://docs.ruby-lang.org/ja/3.4/doc/', 'ja'], ['https://www.gnu.org/software/emacs/manual/html_node/elisp/', 'en']]` | — |
| `en_stopwords` | `['a', 'an', 'the', 'and', 'or', 'but', 'if', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that', 'these', 'those', 'it', 'its', 'i', 'you', 'he', 'she', 'we', 'they', 'them', 'their', 'our', 'your', 'my', 'his', 'her', 'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'each', 'other', 'such', 'into', 'through', 'about', 'than', 'then', 'when', 'where', 'who', 'which', 'what', 'how', 'all', 'any', 'more', 'most', 'also', 'up', 'out', 'as', 'just', 'over', 'after', 'before', 'while', 'since', 'because', 'although', 'however', 'therefore', 'thus', 'hence', 'whether', 'once', 'only', 'even', 'still', 'now', 'here', 'there', 'very', 'too', 'much', 'many', 'some', 'few', 'must', 'let', 'get', 'got', 'make', 'made', 'use', 'used', 'using', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'new', 'old', 'first', 'last', 'long', 'great', 'little', 'own', 'right', 'big', 'high', 'small', 'large', 'next', 'early', 'young', 'important', 'public', 'private', 'real', 'best', 'free', 'same', 'different']` | — |
| `ja_stop_pos` | `['particle', 'auxiliary verb', 'supplementary symbol', 'blank', 'interjection', 'conjunction']` | — |

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

## Keywords

configuration
