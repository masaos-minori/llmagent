---
title: "RAG Query Pipeline - RagPipeline Class Detail (Part 1)"
category: rag
tags:
  - rag-pipeline-class
  - http-mode
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview-part1.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache-part1.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md
---

# RAG クエリパイプライン

- システム概要 → [03_rag_01_system_overview-part1.md](03_rag_01_system_overview-part1.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- 型定義 → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 2. RagPipeline クラス (`scripts/rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError
```

> **ドキュメントと実装の矛盾**: `fetch_full_document` は `rag/pipeline.py` からは提供されない。実体は
> `rag/repository.py` で定義されている（`from rag.repository import fetch_full_document`）。
> `sanitize_document` も同様に `rag/utils.py` の関数であり `rag.pipeline` には存在しない。
> テスト・実装コードでの実際のインポートは `from rag.pipeline import RagPipeline, RagPipelineError` のみ。
> (根拠分類: Explicit in code — `scripts/rag/pipeline.py` のimport文、`scripts/rag/repository.py`の`fetch_full_document()`関数)

このクラスのコンストラクタは `module_cfg` をバイパスして設定します。詳細はソースコードを参照してください。

公開属性および公開メソッドの一覧はソースコードを参照してください。

### 実装意図 (Implementation note)

- `invalidate_cache()` はこのパイプラインインスタンスが認識しているコーパス変更後にのみ呼び出される想定であり、
  呼び出し側（MCPサービス層など）がコーパス変更操作を検知して明示的に呼び出す設計になっている。パイプライン自身が
  DB変更を検知して自動的にキャッシュを無効化する仕組みは持たない (根拠分類: Strongly implied by code — docstringの
  "Call after any corpus-changing operation this pipeline instance is aware of" という記述)。

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_04_query_pipeline-search-stages.md`
- `03_rag_03_05_query_pipeline-augment-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class-part2.md`

## Keywords

rag-pipeline-class
http-mode
rag
