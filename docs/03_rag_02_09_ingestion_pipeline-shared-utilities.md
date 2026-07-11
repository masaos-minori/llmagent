---
title: "Shared Utilities Detail"
category: rag
tags:
  - shared-utilities
  - unicode-normalization
  - cosine-similarity
  - prompt-injection
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_02_01_ingestion_pipeline-overview.md
  - 03_rag_02_02_ingestion_pipeline-crawler.md
  - 03_rag_02_03_ingestion_pipeline-chunksplitter.md
  - 03_rag_02_04_ingestion_pipeline-ingester.md
  - 03_rag_02_07_ingestion_pipeline-utils.md
  - 03_rag_02_08_ingestion_pipeline-shared.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_02_01_ingestion_pipeline-overview.md
---

# RAG インジェクションパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)

---

## 10. Shared Utilities (`scripts/rag/utils.py`)

```python
from rag.utils import (
    cosine_sim,
    floats_to_blob,
    normalize_unicode,
    sanitize_document,
    sanitize_document_full,
    validate_url,
)
```

| 関数 / 定数 | シグネチャ | 戻り値 | 説明 |
|---|---|---|---|
| `normalize_unicode` | `(text: str) -> str` | `str` | NFKC正規化；全角英数字や異体字を変換する |
| `floats_to_blob` | `(values: list[float]) -> bytes` | `bytes` | リトルエンディアンのfloat32 BLOB；sqlite-vecの `MATCH` 演算子の形式。不正な入力に対してTypeError/ValueErrorを発生させる |
| `validate_url` | `(url: str) -> bool` | `bool` | `http`/`https` スキームでnetlocが空でない場合に `True` |
| `cosine_sim` | `(a: list[float], b: list[float]) -> float` | `float` | コサイン類似度；いずれかのベクトルの大きさが0の場合は0.0を返す。SemanticCacheで使用される |
| `sanitize_document` | `(text: str) -> str` | `str` | プロンプトインジェクションパターン（例: "ignore instructions"、"[SYSTEM OVERRIDE]"）を除去する；マッチした部分を `[REMOVED]` に置換する |
| `sanitize_document_full` | `(text: str) -> SanitizeResult` | `SanitizeResult` | sanitize_documentと同様だが監査記録（検出されたパターン、was_sanitizedフラグ）を返す；`was_sanitized: bool`、`patterns: list[str]`、`sanitized_text: str` を持つSanitizeResult dataclassを返す |

**定数:**

| 定数 | 値 | 説明 |
|---|---|---|
| `MIN_TEXT_LENGTH_FOR_DETECTION` | `100` | 言語判定に必要な最小テキスト長；これより短いページはヒント言語を使用する；crawler_utilsの `detect_lang()` でも使用される |
| `LOG_KEY_URL` | `"url"` | URL用の構造化ログフィールドキー |
| `LOG_KEY_DOC_ID` | `"doc_id"` | ドキュメントID用の構造化ログフィールドキー |
| `LOG_KEY_CHUNK_ID` | `"chunk_id"` | チャンクID用の構造化ログフィールドキー |
| `LOG_KEY_SOURCE_TYPE` | `"source_type"` | ソースタイプ（http/file）用の構造化ログフィールドキー |
| `LOG_KEY_STAGE_NAME` | `"stage_name"` | ステージ名用の構造化ログフィールドキー |

**プロンプトインジェクションパターン:**

| パターン | 正規表現 | 説明 |
|---|---|---|
| Ignore instructions | `(?i)(ignore\s+(?:(?:all\|previous)\s+)*instructions?)` | "ignore all instructions"、"ignore previous instructions" などを捕捉する |
| System prefix | `(?i)(system\s*:\s*)` | "system:" というプレフィックスを捕捉する |
| SYSTEM OVERRIDE | `(?i)\[SYSTEM\s*OVERRIDE\]` | "[SYSTEM OVERRIDE]" を捕捉する |
| Disregard instructions | `(?i)(disregard\s+(?:(?:all\|prior\|previous)\s+)*instructions?)` | "disregard all instructions" などを捕捉する |
| New instructions | `(?i)(new\s+instructions?:)` | "new instructions:" などを捕捉する |

**構造化ログキー（RAGライフサイクルのトレース）:**

| キー | 値 | 使用元 |
|---|---|---|
| `url` | URL文字列 | crawler、ingester |
| `doc_id` | INTEGER型のドキュメントID | ingester |
| `chunk_id` | INTEGER型のチャンクID | ingester（chunks_vec挿入経由） |
| `source_type` | `"http"` / `"file"` | crawler、ingester |
| `stage_name` | スクリプト名（"ingester"） | ingester |

**利用元:**

| スクリプト | 使用される関数 |
|---|---|
| `scripts/rag/ingestion/chunk_splitter.py` | `normalize_unicode` |
| `scripts/rag/ingestion/chunk_japanese.py` | `normalize_unicode` |
| `scripts/rag/ingestion/ingester.py` | `floats_to_blob`, `validate_url` |
| `scripts/rag/ingestion/crawler.py` | `validate_url` |
| `scripts/rag/pipeline.py` | `sanitize_document`, `floats_to_blob` |
| `scripts/rag/cache.py` | `cosine_sim` |

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview.md`
- `03_rag_02_01_ingestion_pipeline-overview.md`
- `03_rag_02_02_ingestion_pipeline-crawler.md`
- `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- `03_rag_02_04_ingestion_pipeline-ingester.md`
- `03_rag_02_07_ingestion_pipeline-utils.md`
- `03_rag_02_08_ingestion_pipeline-shared.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

shared-utilities
unicode-normalization
cosine-similarity
prompt-injection
rag
