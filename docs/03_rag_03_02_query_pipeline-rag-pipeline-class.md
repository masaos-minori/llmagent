---
title: "RAG Query Pipeline - RagPipeline Class Detail"
category: rag
tags:
  - rag-pipeline-class
  - http-mode
related:
  - 03_rag_00_document-guide.md
  - 03_rag_01_system_overview.md
  - 03_rag_03_01_query_pipeline-overview.md
  - 03_rag_03_03_query_pipeline-context-and-diagnostics.md
  - 03_rag_03_query_pipeline-stages.md
  - 03_rag_03_06_query_pipeline-helpers-and-cache.md
  - 03_rag_04_05_dto-types.md
  - 03_rag_05_1-configuration-reference.md
source:
  - 03_rag_03_01_query_pipeline-overview.md
---

# RAG クエリパイプライン

- システム概要 → [03_rag_01_system_overview.md](03_rag_01_system_overview.md)
- 設定 → [03_rag_05_1-configuration-reference.md](03_rag_05_1-configuration-reference.md)
- 型定義 → [03_rag_04_05_dto-types.md](03_rag_04_01_dto-models_data.md)

---

## 2. RagPipeline クラス (`scripts/rag/pipeline.py`)

```python
from rag.pipeline import RagPipeline, RagPipelineError, fetch_full_document, get_embedding
from rag.utils import sanitize_document
```

### コンストラクタ

| パラメータ | 型 | 説明 |
|---|---|---|
| `http` | `httpx.AsyncClient` | LLM/埋め込み呼び出し用のHTTPクライアント |
| `cfg` | `RagConfig` | agent.tomlから読み込まれるRAG設定 |
| `module_cfg` | `dict \| None` | 任意の設定オーバーライド；load_all() / agent.toml（エージェントプロセス経路）をバイパスする；Noneの場合は内部モジュール設定の取得にフォールバックする |
| `on_status` | `Callable[[str], None] \| None` | 進行状況コールバック；デフォルトはno-op |
| `on_clear` | `Callable[[], None] \| None` | クリーンアップコールバック；`run()`/`augment()` の `finally` ブロックで常に呼び出される |

```python
RagPipeline(
    http: httpx.AsyncClient,
    cfg: RagConfig,
    *,
    module_cfg: dict | None = None,
    on_status: Callable[[str], None] | None = None,
    on_clear: Callable[[], None] | None = None,
)
```

### 公開属性

| 属性 | 型 | 説明 |
|---|---|---|
| `last_fetch_result` | `TwoStageFetchResult \| None` | 直前の `run()`/`augment()` によるリランク済みヒット。`hits`、`min_score_applied`、`max_chunks_per_doc` を保持する |
| `last_timings` | `dict[str, float]` | 直前の `run()` の各ステージの実測秒数 |
| `last_stage_results` | `list[StageResult]` | 直前の `run()` のステージごとの結果記録（status、fallback reason、elapsed） |
| `semantic_cache` | `SemanticCache` | インメモリの最近傍キャッシュ |
| `last_search_diagnostics` | `SearchDiagnostics` | 直前の `run()` の検索診断情報；HTTPモード用に `result_source`、`http_result_kind`、`remote_status_code`、`remote_latency_ms`、`fallback_reason` を含む |
| `stat_search_embed_failed` | `int` | このインスタンス上のすべての `run()` 呼び出しにおける埋め込み失敗の累積数 |
| `stat_search_fts_errors` | `int` | このインスタンス上のすべての `run()` 呼び出しにおけるFTSエラーの累積数 |

### 公開メソッド

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `run` | `async (query, db, history_context="", hook_strict=False) -> PipelineRunResult` | MQE→search→RRF→rerank+PluginHooksを実行する；`PipelineRunResult`（queries、search_results、merged、reranked、stage_results、diagnostics）を返す；**`result_source` は設定しない** — ローカルモードでは常に `None`；`hook_strict=True` の場合は最初のプラグインフック失敗を再送出する（デフォルト: 警告をログに記録しスキップ）；`finally` で常に `on_clear()` を呼び出す |
| `augment` | `async (query, debug_fn=None, history_context="") -> str` | パイプライン全体 + Augmentステージを実行する；コンテキストブロック文字列または `""` を返す；DB失敗時は `RagPipelineError` を発生させる |
| `search_queries` | `async (queries, db) -> list[list[RagHit]]` | 単独利用可能なヘルパー: 並列埋め込み + 逐次DB検索；`SearchDiagnostics` を記録するSearchStageとは異なり、**診断情報を記録しない** |
| `rerank_candidates` | `async (query, merged) -> list[RagHit]` | 単独利用可能なヘルパー: クロスエンコーダ、またはスライス+重複排除によるフォールバック + 重複排除 |
| `get_diagnostics` | `() -> dict` | 直前のパイプライン実行に関する構造化された診断情報を返す；`run()`/`augment()` の前に呼び出しても安全 — 空/ゼロ値を返す |

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
- `03_rag_01_system_overview.md`
- `03_rag_03_01_query_pipeline-overview.md`
- `03_rag_03_03_query_pipeline-context-and-diagnostics.md`
- `03_rag_03_query_pipeline-stages.md`
- `03_rag_03_06_query_pipeline-helpers-and-cache.md`
- `03_rag_04_05_dto-types.md`
- `03_rag_05_1-configuration-reference.md`

## Keywords

rag-pipeline-class
http-mode
rag
