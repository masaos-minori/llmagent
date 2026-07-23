---
title: "6.1 models_data.py (`scripts/rag/models_data.py`)"
category: rag
tags:
  - rag
  - dto
  - data-model
related:
  - 03_rag_00_document-guide.md
  - 03_rag_04_05_dto-types.md
source:
  - 03_rag_04_05_dto-types.md
---

# 6.1 models_data.py (`scripts/rag/models_data.py`)

## データ構造の目的

このファイルはRAGパイプライン全体で共有されるデータモデルを定義する。
すべてのDTOは `@dataclass(frozen=True)` として定義されており、生成後の書き換えを禁止する。

## 設計上重要なフィールド

### EmbeddingResponse — 埋め込みAPIからのレスポンス
- `embedding`: 埋め込みベクトル（必須）
- `model`: モデル名（省略可）

### CrawlTarget — WebCrawlerのクロール対象
- `url`: クロール対象URL（必須）
- `lang`: 言語ヒント（`LanguageCode` enum、`"en"`/`"ja"`）

### ChunkDocument — パイプラインステージ間で受け渡されるチャンクデータ
- `url`, `title`, `lang`, `content`: 必須フィールド
- `etag`, `last_modified`: 更新検知用
- `normalized_content`: Sudachi正規化済みテキスト（日本語のみ）
- `chunking_strategy`, `source_file`, `chunk_type`: 処理メタデータ

### ChunkRecord — 埋め込みベクトル付きチャンク（クエリパイプライン使用）
- `chunk_id`, `url`, `title`, `lang`, `content`: 必須フィールド
- `embedding`: 埋め込みベクトル

### CacheEntry — セマンティックキャッシュエントリ
- `embedding`, `context_str`: 必須フィールド
- `history_context`: 関連会話履歴
- `generation`: キャッシュ無効化用世代カウンタ

### TwoStageFetchResult — HTTP RAGサービス呼び出し結果
- `hits`: インプロセス時は `RagHit`、HTTPモード時は `dict`（型が異なる）
- `min_score_applied`, `max_chunks_per_doc`: フィルタリングパラメータ

## 永続化・検索・互換性に関わる制約

- `ChunkDocument.normalized_content` は日本語のみ有効
- `TwoStageFetchResult.hits` の要素型は呼び出しモードによって異なる（`RagHit` / `dict`）
- `CrawlTarget.lang` は `LanguageCode` enum、他DTOの `lang` は素の `str`（型不統一に注意）

## Related Documents

- [03_rag_04_05_dto-types.md](03_rag_04_05_dto-types.md)
- [03_rag_00_document-guide.md](03_rag_00_document-guide.md)

## Keywords

dto
data-model
frozen-dataclass
LanguageCode
