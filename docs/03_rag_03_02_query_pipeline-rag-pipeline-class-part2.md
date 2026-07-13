---
title: "RAG Query Pipeline - RagPipeline Class Detail (Part 2)"
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

> **ドキュメントと実装の矛盾**: `fetch_full_document`（`rag/repository.py`）と `sanitize_document`
> （`rag/utils.py`）は `rag.pipeline` からは提供されない。詳細は
> [Part 1](03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md) 参照。
> (根拠分類: Explicit in code)

### HTTPモード（`rag_service_url`）

`rag_service_url` が空でない場合、`augment()` はインプロセスパイプラインを実行する代わりに、
`scripts/rag/pipeline_service.py` の `call_rag_service()` を介して外部RAGサービスに委譲する。

| 動作 | 詳細 |
|---|---|
| 認証 | `rag_auth_token != ""` の場合、`X-RAG-Token: {rag_auth_token}` ヘッダが付加される（デフォルト: ヘッダなし） |
| タイムアウト | HTTP試行1回あたり10.0秒（接続+読み取り） |
| リトライ | 5xxまたはトランスポートエラーの場合は最大2回リトライ；指数バックオフ（1秒、2秒）；4xxまたはJSONパースエラーではリトライしない |
| フォールバック | `None` が返された場合 → インプロセスパイプライン；`""`（空のコンテキスト）→ 有効な結果として受理される |
| 無限委譲の防止 | MCPアダプタは `rag_service_url=""` をハードコードしているため、インプロセスの `augment()` が再度委譲することはない |
| 戻り値 | `call_rag_service()` は `(context: str \| None, status_code: int \| None, elapsed_ms: float)` を返す — `status_code` と `elapsed_ms` は診断情報として利用可能 |

`RagConfig` Protocol（`shared/types.py`）の設定フィールド:
- `rag_service_url: str` — リモートエンドポイントのURL；空文字列の場合HTTPモードは無効
- `rag_auth_token: str` — `X-RAG-Token` ヘッダ用の任意のベアラートークン；`""` = 認証なし（デフォルト）

#### call_rag_service() 関数 (`scripts/rag/pipeline_service.py`)

```python
call_rag_service(
    http: httpx.AsyncClient,
    rag_url: str,
    query: str,
    history_context: str,
    *,
    auth_token: str = "",
    set_fetch_result: Callable[[TwoStageFetchResult], None],
    set_fallback_reason: Callable[[str], None] | None = None,
) -> tuple[str | None, int | None, float]
```

戻り値の契約:

| 戻り値 | 条件 |
|---|---|
| `str`（非空） | HTTP 200 かつレスポンスボディに空でない文字列値を持つ `"result"` キーがある |
| `""`（空文字列） | HTTP 200だが `"result"` キーが存在しない、None、または空 — 有効な空の結果 |
| `None` | HTTP 4xx（リトライなし）、リトライを使い切った5xx、トランスポートエラー、またはJSONパースエラー — インプロセスへのフォールバックを発生させる |

副作用:
- `set_fetch_result` は、レスポンスボディから取得したフェッチステージのステータスとヒットを保持する `TwoStageFetchResult` と共に呼び出される
- `set_fallback_reason` は、成功以外の経路（4xx、トランスポートエラーなど）で理由文字列と共に呼び出される

`rag_service_url` が設定されている場合、`augment()` はHTTP結果を分類し、
`get_diagnostics()["http_result_kind"]` と `StageResult.fallback_reason` に記録する。

| `http_result_kind` | `StageResult` のstatus | `fallback_reason` | 条件 |
|---|---|---|---|
| `"remote_nonempty"` | `"success"` | `None` | HTTP呼び出しが成功；非空のコンテキストが返された |
| `"remote_empty"` | `"success"` | `None` | HTTP 200だがcontextフィールドが `""` — 有効な空の結果であり、フォールバックではない |
| `"in_process_fallback"` | `"fallback"` | エラー文字列 | HTTPエラー；代わりにインプロセスのRAGパイプラインが実行された |
| `None` | — | — | `rag_service_url` が未設定；HTTPモードは使用されていない |

`"remote_empty"` のケースはフォールバックではなく**成功**である。リモートサービスは
HTTP 200で応答したが、関連コンテキストが見つからなかった。この場合、インプロセスパイプラインは
実行されない。実際のフォールバック事象と混同しないよう、`remote_nonempty` と `remote_empty` の両方で
`fallback_reason` は `None` になる。

この分類結果は以下で確認できる。
- `get_diagnostics()["http_result_kind"]`
- `/rag search --debug`: `[debug] http mode: result_source=remote http_result_kind=success (empty response — no in-process fallback)`

> **注意**: `get_diagnostics()["http_result_kind"]`（値: `remote_nonempty`/`remote_empty`/`in_process_fallback`）と
> `SearchDiagnostics.http_result_kind`（`rag.models_result.HttpResultKind` enum、値:
> `success`/`empty`/`error`/`not_used`）は名前は似ているが異なる語彙を持つ別々のフィールドである。
> 詳細は [03_rag_03_03_query_pipeline-context-and-diagnostics.md](03_rag_03_03_query_pipeline-context-and-diagnostics.md) §4.2 参照。
> (根拠分類: Explicit in code — `scripts/rag/http_augment.py:25-32`, `scripts/rag/pipeline.py:485-499`)

#### HTTP RAGリクエストの詳細

| 項目 | 値 |
|---|---|
| エンドポイント | `{rag_url}/v1/call_tool` |
| リクエストボディ | `{"name": "rag_run_pipeline", "args": {"query": query, "history_context": [history_context]}}`（history_contextが空の場合は空リスト） |
| 最大試行回数 | 合計3回（初回 + 2回のリトライ） |
| リトライのバックオフ | 指数的: `min(2**attempt, 5)` 秒 |

---

## Related Documents

- `03_rag_00_document-guide.md`
- `03_rag_01_system_overview-part1.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache-part1.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`
- `03_rag_03_02_query_pipeline-rag-pipeline-class-part1.md`

## Keywords

rag-pipeline-class
http-mode
rag
