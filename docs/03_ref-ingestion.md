# 取込パイプライン — API リファレンス (インデックス + 共通実装注意事項)

実行ガイド → [`docs/03_ingestion-run.md`](03_ingestion-run.md)

## 各スクリプト API リファレンス

| ファイル | 内容 |
|---|---|
| [03_ref-crawler.md](03_ref-crawler.md) | `rag/ingestion/crawler.py` API |
| [03_ref-splitter.md](03_ref-splitter.md) | `rag/ingestion/chunk_splitter.py` API |
| [03_ref-ingester.md](03_ref-ingester.md) | `rag/ingestion/ingester.py` API |

---

## 5. 実装注意事項

取込パイプライン全体にわたる実装上の注意点をまとめる。

### 5.1 パイプラインデータフロー

```
config/rag_pipeline.json の target_urls
  → web_crawler.py:    BFS クロール (同一オリジン) → rag-src/yyyymmddhhmmss-{slug}.txt
  → chunk_splitter.py: チャンク分割
                       JA: Sudachi / EN: sentence split / code: 空行区切り
                       → rag-src/chunk/{stem}-{idx:04d}.txt
  → rag_ingester.py:   embed (passage: prefix) → SQLite INSERT → rag-src/registered/
```

### 5.2 FTS5 クエリ Sudachi フィルタ

`rag/repository.py` の `_build_fts_query()` は日本語クエリを `_build_fts_tokens_ja()` で処理し、名詞・動詞・形容詞の `normalized_form()` のみを FTS5 トークンとして使用する。`chunks_fts` は `normalized_content` (正規化形スペース結合) でインデックスされているため、クエリも同じ正規化形で照合する必要がある。Sudachi は `_get_sudachi_tokenizer()` で遅延初期化 (import 時の副作用ゼロ)。英語クエリは regex トークン化のまま。

### 5.3 FTS5 / LLM コンテンツ分離

日本語チャンクは `chunks.content` に原文、`chunks.normalized_content` に Sudachi normalized_form スペース結合形を格納する。FTS5 の `chunks_ai` / `chunks_au` / `chunks_ad` トリガが `COALESCE(normalized_content, content)` を `chunks_fts` に書き込む。LLM には `chunks.content` (原文) が渡り、BM25 検索は `normalized_content` でマッチする。英語・コードは `normalized_content = NULL` のため FTS5 は `content` をそのまま使用する。
