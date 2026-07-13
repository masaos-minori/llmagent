---
title: "5. Constraints Reference"
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

# 5. 制約リファレンス

## 5. 制約リファレンス

| Constraint | Value |
|---|---|
| 言語判定の閾値 | CJK比率 ≥ 0.10 → `ja`; ページが100文字未満 → ヒント言語を使用 |
| チャンクサイズの範囲 | 40〜500文字 (`config/chunk_splitter.toml`の`min_chunk`/`max_chunk`で設定可能) |
| チャンクの重複 | 50文字のスライディングウィンドウ (`config/chunk_splitter.toml:chunk_overlap`) |
| 埋め込みの次元数 | 384 (`config/agent.toml:embedding_dims`、および`config/ingester.toml:embedding_dims`)。float32リトルエンディアンBLOB |
| クロール深度 | コードのデフォルトは`max_depth`未指定不可 (`config/crawler.toml`必須キー)。運用中の`config/crawler.toml`では`max_depth = 3` |
| クロールページ数の上限 | コードのデフォルトはサイトごと500ページ (`crawler.py`の`cfg.get("max_pages", 500)`)。運用中の`config/crawler.toml`では`max_pages = 200` |
| レプリカ | 単一ノードのSQLiteのみ |

**根拠:**
- CJK閾値・文字数閾値・チャンクサイズ/重複・埋め込み次元/エンディアンは Explicit in code (`scripts/rag/ingestion/crawler_utils.py`, `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/utils.py:floats_to_blob`, `config/agent.toml`, `config/ingester.toml`)。
- クロール深度・ページ数上限は Explicit in code だが、コードの既定値と実際に運用されている`config/crawler.toml`の値が異なる。旧版では「`config/agent.toml:43`」「最大6ホップ」「最大500ページ」と記載されていたが、現行の`config/agent.toml`では`embedding_dims`は17行目であり、`config/crawler.toml`実値は`max_depth=3`, `max_pages=200`である。行番号・値は設定変更で容易にずれるため、参照は「セクション名」ベースに修正した。

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- [03_rag_05_7-rag-index-consistency-checks.md](03_rag_05_7-rag-index-consistency-checks.md)

## Keywords

configuration
constraints
chunking
embedding-dims
