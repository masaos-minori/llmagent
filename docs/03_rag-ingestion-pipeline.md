# 取込パイプライン

- [実行ガイド](03_rag-ingestion-run.md) — 実行コマンド・ファイルライフサイクル

## 各スクリプト API リファレンス

| ファイル | 内容 |
|---|---|
| [03_rag-ref-crawler.md](03_rag-ref-crawler.md) | `rag/ingestion/crawler.py` API |
| [03_rag-ref-splitter.md](03_rag-ref-splitter.md) | `scripts/rag/ingestion/chunk_splitter.py` API |
| [03_rag-ref-ingester.md](03_rag-ref-ingester.md) | `scripts/rag/ingestion/ingester.py` API |
| [03_rag-ref-mdq.md](03_rag-ref-mdq.md) | `mcp/mdq/` API |

---

## rag/utils.py

### 機能概要

RAG 取込パイプライン (`rag/ingestion/crawler.py`, `rag/ingestion/chunk_splitter.py`, `rag/ingestion/ingester.py`) とベクトル検索 (`rag/pipeline.py`) で共用するテキスト処理ユーティリティ。

### API

```python
from rag.utils import normalize_unicode, floats_to_blob, validate_url
```

| 関数 | 引数 | 戻り値 | 説明 |
|---|---|---|---|
| `normalize_unicode(text)` | `text: str` | `str` | NFKC 正規化。全角英数字・異体字を標準形に変換 |
| `floats_to_blob(values)` | `values: list[float]` | `bytes` | float リストを little-endian float32 BLOB に変換 |
| `validate_url(url)` | `url: str` | `bool` | `http`/`https` スキームかつ netloc が空でない場合に `True` を返す |

### 実装注意

`floats_to_blob` は sqlite-vec の `MATCH` 演算子が要求するバイト形式 (little-endian float32 = `struct.pack("<{N}f", ...)`) で出力。埋込次元が 384 の場合、出力は 384 × 4 = 1536 バイト。

### 使用スクリプト

| スクリプト | 使用関数 |
|---|---|
| `rag/ingestion/chunk_splitter.py` | `normalize_unicode` |
| `rag/pipeline.py` | `floats_to_blob` |
| `rag/ingestion/ingester.py` | `floats_to_blob`, `validate_url` |
| `rag/ingestion/crawler.py` | `validate_url` |

---

## 実装注意事項

### パイプラインデータフロー

```
config/rag_pipeline.toml の target_urls
  → scripts/rag/ingestion/crawler.py:    BFS クロール (同一オリジン) → rag-src/yyyymmddhhmmss-{slug}.txt
  → scripts/rag/ingestion/chunk_splitter.py: チャンク分割
                       JA: Sudachi / EN: sentence split / code: 空行区切り
                       → rag-src/chunk/{stem}-{idx:04d}.txt
  → scripts/rag/ingestion/ingester.py:   embed (passage: prefix) → SQLite INSERT → rag-src/registered/
```

### FTS5 クエリ Sudachi フィルタ

`rag/repository.py` の `_build_fts_query()` は日本語クエリを `_build_fts_tokens_ja()` で処理し、名詞・動詞・形容詞の `normalized_form()` のみを FTS5 トークンとして使用する。`chunks_fts` は `normalized_content` (正規化形スペース結合) でインデックスされているため、クエリも同じ正規化形で照合する必要がある。Sudachi は `_get_sudachi_tokenizer()` で遅延初期化 (import 時の副作用ゼロ)。英語クエリは regex トークン化のまま。

### FTS5 / LLM コンテンツ分離

日本語チャンクは `chunks.content` に原文、`chunks.normalized_content` に Sudachi normalized_form スペース結合形を格納する。FTS5 の `chunks_ai` / `chunks_au` / `chunks_ad` トリガが `COALESCE(normalized_content, content)` を `chunks_fts` に書き込む。LLM には `chunks.content` (原文) が渡り、BM25 検索は `normalized_content` でマッチする。英語・コードは `normalized_content = NULL` のため FTS5 は `content` をそのまま使用する。
