---
title: "4. Error Handling Reference"
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

# 4. エラー処理リファレンス

## 4. エラー処理リファレンス

### Crawler

| Error | Action |
|---|---|
| HTTP失敗 | `fetch_retry`まで指数バックオフ (`min(2**i, 10)` 秒) で再試行 |
| URL単位の例外 | `WARNING` を出して継続 |
| `lang`が`ja`/`en`以外 | URLをスキップ |

### ChunkSplitter

| Error | Action |
|---|---|
| Sudachiのトークナイズエラー | `""`を返却; チャンクをスキップ; `WARNING` |
| ファイル単位の失敗 | `ERROR` (トレースバック付き); 次のファイルへ継続 |
| 既存チャンク | `--force`指定がない限りスキップ |

### RagIngester

| Error | Action |
|---|---|
| 埋め込みAPIの失敗 | `embed_retry`まで指数バックオフで再試行 |
| リトライ上限到達 (単一チャンク) | `WARNING`; チャンクをスキップ; 継続 |
| `lang`の値が不正 | `ValueError`; URLグループをスキップ; `ERROR` (トレースバック付き) |

### RagPipeline

| Error | Action |
|---|---|
| DBオープンエラー | `RagPipelineError`を発生 (`""`を返却しない) |
| `use_search=False` | 即座に`""`を返却 |
| `rag_service_url`設定時に失敗 | インプロセスパイプラインにフォールバック |
| クロスエンコーダーの失敗 | `RagRerankError`は`RuntimeError`として捕捉され、`StageResult.status="failure"`が記録され、警告がログに出力される。パイプラインは`ctx.reranked=[]`のまま継続する (RRFへのフォールバックはない)。`use_rerank=False`の場合はRRFの順序と重複排除が代わりに使用される。 |

### 実装上の補足

- `RagRerankError`は`scripts/rag/exceptions.py`ではなく`scripts/rag/llm_prompts.py`に
  `class RagRerankError(RuntimeError)`として定義されている。`RuntimeError`のサブクラスなので、
  `pipeline.py`の`_run_stage()`が捕捉する例外タプル (`RuntimeError`, `sqlite3.OperationalError`,
  `httpx.HTTPStatusError`, `httpx.RequestError`, `TimeoutError`) に含まれ、
  「`RuntimeError`として捕捉される」という記述は正確。
  [Explicit in code]
- `scripts/rag/exceptions.py`で定義されている実際の例外クラスは
  `RagLayerError` (基底) / `EmbeddingSchemaError` / `PipelineValidationError` /
  `SearchQueryError` / `ChunkFormatError` / `TokenizationError` / `UnknownMetadataError`
  の7種であり、`RagRerankError`や`RagPipelineError`はここには含まれない
  (両者はそれぞれ`llm_prompts.py`, `pipeline.py`に個別定義)。
  例外階層はrag層全体で単一の基底クラスに統一されているわけではない。
  [Explicit in code]
- `RagPipeline.__init__()`は起動時に`RagConfigValidator().validate()`
  (`shared/config_validator.py`) を実行し、`result.ok`が`False`の場合は
  `ValueError`を送出してインスタンス生成自体を中断する。警告 (`result.warnings`) は
  ログに出力されるのみで継続可能。
  [Explicit in code] — 本節にはこの初期化時バリデーションの記載がなかったため補足。

---


## Related Documents

- [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- [03_rag_04_04_dto-models_config.md](03_rag_04_04_dto-models_config.md)

## Keywords

configuration
exception-hierarchy
