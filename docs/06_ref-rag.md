# RAG パイプラインモジュール

RAG (Retrieval-Augmented Generation) パイプライン全ステップを実装するモジュール。

| モジュール | 役割 |
|---|---|
| `rag/pipeline.py` | `RagPipeline` / `RagPipelineError` — MQE / KNN+BM25 検索 / RRF / Cross-Encoder 再ランクのオーケストレーション; `sanitize_document` を `rag.utils` から re-export |
| `rag/repository.py` | `RagRepository` / `RagScorer` / スタンドアロンヘルパー関数群; `SemanticCache` / `cosine_sim` は `rag.cache` / `rag.utils` から backward compat re-export |
| `rag/cache.py` | `SemanticCache` (canonical) / `CacheService` Protocol — dimension 検証付き in-memory キャッシュ |
| `rag/llm.py` | `RagLLM` / `MqeParseError` / `RagExpansionError` / `RagRerankError` / `get_embedding` / `summarize_tool_result` |
| `rag/types.py` | `RawHit` / `MergedHit` / `RankedHit` TypedDict; `RagHit` Union alias; `PipelineStageResult` / `RagQuery` dataclass; `LLMMessage` を `shared/types.py` から re-export |
| `shared/types.py` | `RagConfig` Protocol — `RagPipeline` が要求する設定フィールドの構造的型定義 |

---

## 1. rag/pipeline.py

### 1.1 機能概要

RAG パイプラインの全ステップを実装するモジュール。`RagPipeline` クラスがパイプライン全体をオーケストレーションし、`mcp/rag_pipeline/service.py` から呼び出される。agent 本体 (`agent/repl.py`) は直接参照しない。

パイプライン実行順:

```
[1] MQE     — RagLLM.expand_queries:         クエリを N 通りに言い換えて再現率を向上させる
[2] Search  — get_embedding /                 埋込ベクトルを生成し KNN + BM25 で検索する
              RagRepository.vector_search /
              RagRepository.fts_search
[3] RRF     — RagScorer.rrf_merge:            複数クエリの結果リストを RRF スコアで統合する
[4] Rerank  — RagLLM.cross_encoder_rerank:    LLM が候補チャンクを関連度スコアで再順位付けする
```

クラス層 (関心の分離):

| クラス | 責務 |
|---|---|
| `RagRepository` | すべての SQL をここに閉じ込める。`vector_search` / `fts_search` を提供し、呼び出しごとに `top_k` / `hits` / `elapsed_ms` 等をログ出力する (`vector_search` は `query` をログしない; `fts_search` は `query` / `fts_query` / `top_k` / `hits` / `elapsed_ms` をログ出力する) |
| `RagScorer` | スコア融合 (RRF)。`rrf_merge` を静的メソッドとして提供する |
| `RagLLM` | LLM 呼び出し (MQE クエリ拡張 + クロスエンコーダ再ランク)。共通 `_call_llm()` に HTTP 処理を集約する |

公開 API は `__all__` に列挙: `RagPipeline` / `RagHit` / `fetch_full_document` / `get_embedding`。その他のクラス (`RagRepository`, `RagScorer`, `RagLLM`, `SemanticCache`) は `rag/repository.py` / `rag/llm.py` に実装し `rag/pipeline.py` からインポートして re-export する。

`run()` の RRF ステップは `cfg.use_rrf=True` のとき `RagScorer.rrf_merge` を呼び出す。`use_rrf=False` のときは `_dedup_hits(all_results)` にフォールバックし、`chunk_id` をキーに先着順で重複排除し全チャンクに `rrf_score=0.0` を付与する。

`run()` 実行後にプラグインポストステージが順次適用される。`plugin_registry.get_pipeline_post_stages()` で登録済みのコールバックが `(reranked, query)` を受け取り、フィルタまたは並び替えを行う。各ステージの例外は `logger.warning` で記録してスキップされる。

### 1.2 API

```python
import httpx
from rag.pipeline import RagPipeline, fetch_full_document, get_embedding
from rag.repository import RagRepository, RagScorer, SemanticCache, deduplicate_chunks, cosine_sim
from rag.llm import RagLLM

# SemanticCache は rag.repository から直接 import する (rag.pipeline の __all__ に含まれない)
from rag.repository import SemanticCache
```

#### RagPipeline

```python
RagPipeline(
    http: httpx.AsyncClient,
    cfg: RagConfig,
    on_status: Callable[[str], None] | None = None,
    on_clear: Callable[[], None] | None = None,
)
```

| 属性 / メソッド | 説明 |
|---|---|
| `last_reranked: list[RagHit]` | 直前の `run()` / `augment()` が生成した再ランク済みヒットリスト (二段階取得用) |
| `last_timings: dict[str, float]` | 直前の `run()` 呼び出しのステップ別壁時計秒 (`rag.mqe` / `rag.search` / `rag.rrf` / `rag.rerank`) |
| `semantic_cache: SemanticCache` | インメモリ最近傍キャッシュ (`cfg.semantic_cache_max_size` / `cfg.semantic_cache_threshold` で初期化) |
| `expand_queries_safe(query, context="") -> list[str]` | `cfg.use_mqe=False` のとき `[query]` を即返す。MQE 失敗時も `[query]` にフォールバック |
| `search_queries(queries, db) -> list[list[RagHit]]` | 埋込生成を並行実行し、DB 検索を逐次実行 (接続競合回避)。各クエリで `vector_search` + `fts_search` の結果をそれぞれ `all_results` に追加 |
| `rerank_candidates(query, merged) -> list[RagHit]` | `cfg.use_rerank=False` のとき RRF 順で `rag_top_k` 件を返す。クロスエンコーダ失敗時も RRF 順にフォールバック。`deduplicate_chunks` で後処理 |
| `run(query, db, history_context="") -> tuple[list[str], list[list[RagHit]], list[RagHit], list[RagHit]]` | MQE→検索→RRF (または `_dedup_hits`)→再ランクを実行; `(queries, all_results, merged, reranked)` を返す; `finally` で必ず `on_clear()` を呼ぶ; プラグインポストステージを全て適用後に `last_reranked` を更新する |
| `augment(query, debug_fn=None, history_context="") -> str` | パイプラインを実行してコンテキストブロック文字列を返す。`use_search=False` または結果なし時は `""`。`cfg.rag_service_url` が設定されていれば `_augment_http()` で外部 RAG サービスに委譲し、失敗時のみ in-process にフォールバック。`use_refiner=True` のとき `_augment_refiner()` でチャンクを圧縮し、空出力・例外時はそのまま生チャンクを返す |

クラス層 API:

| クラス | メソッド | シグネチャ | 説明 |
|---|---|---|---|
| `RagRepository(db)` | `vector_search` | `(embedding: list[float], top_k: int) -> list[RagHit]` | KNN 検索; `top_k` / `hits` / `elapsed_ms` をログ出力 (`query` はログしない) |
| | `fts_search` | `(query: str, top_k: int) -> list[RagHit]` | BM25 検索; `sqlite3.OperationalError` (syntax error 等) 時は `[]` を返す; `query` / `fts_query` / `top_k` / `hits` / `elapsed_ms` をログ出力 |
| `RagScorer` | `rrf_merge` (static) | `(results_list: list[list[RagHit]], rrf_k: int = 60) -> list[RagHit]` | RRF スコア `Σ 1/(rrf_k+rank)` で結果リストを統合; `rrf_score` フィールドを付与して降順で返す |
| `RagLLM(client, llm_url)` | `expand_queries` | `(query: str, context: str = "") -> list[str]` | MQE クエリ拡張。失敗時は `[query]` を返す |
| | `cross_encoder_rerank` | `(query: str, candidates: list[RagHit], top_k: int, rag_min_score: float = 0.0) -> list[RagHit]` | クロスエンコーダ再ランク; `rag_min_score` 未満を除外; 失敗時は RRF 順で `top_k` を返す |
| | `summarize_tool_result` | `(text: str, tool_name: str, args: dict) -> str` | ツール結果を LLM で要約して返す。失敗時は元 `text` を返す |
| | `refine_context` | `(chunks: list[RagHit], query: str, max_tokens: int, per_chunk_chars: int, timeout: float) -> str` | Rerank 後チャンクをクエリ関連要点に圧縮して返す; エラー時は呼び出し元で fallback |

`RagPipeline` プライベートメソッド (内部実装):

| メソッド | シグネチャ | 説明 |
|---|---|---|
| `_augment_http` | `(rag_url: str, query: str, history_context: str) -> str \| None` | `{rag_url}/v1/search` に POST して外部 RAG サービスの結果を取得; ヒットがあれば `last_reranked` を更新; 失敗時は `None` を返し in-process フォールバックを促す |
| `_augment_refiner` | `(reranked: list[RagHit], query: str) -> str \| None` | `RagLLM.refine_context` を呼び出してチャンクを圧縮; 空出力・例外時は `None` を返す |
| `_format_chunks` (static) | `(reranked: list[RagHit]) -> str` | reranked ヒットを `[Source: title \| url]\ncontent` 形式のブロックに整形し `---` 区切りで連結する |

`rag/repository.py` 公開関数 (モジュールレベル):

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `vector_search` | `(embedding: list[float], top_k: int, db: SQLiteHelper) -> list[RagHit]` | `RagRepository(db).vector_search()` に委譲するスタンドアロンラッパー |
| `fts_search` | `(query: str, top_k: int, db: SQLiteHelper) -> list[RagHit]` | `RagRepository(db).fts_search()` に委譲するスタンドアロンラッパー |
| `fetch_full_document` | `(chunk_id: int, db: SQLiteHelper, window: int \| None = None) -> list[RagHit]` | 指定チャンクと同じドキュメントのチャンクを `chunk_index` 昇順で返す。`window=None` で全件、`window=N` で ±N 件 (二段階取得用) |
| `deduplicate_chunks` | `(hits: list[RagHit], max_per_doc: int) -> list[RagHit]` | URL をキーに同一ドキュメントのチャンクを `max_per_doc` 件に絞る。入力は降順ソート済みであること |
| `cosine_sim` | `(a: list[float], b: list[float]) -> float` | 2 つの埋込ベクトルのコサイン類似度を返す。どちらかが零ベクトルなら `0.0` を返す (セマンティックキャッシュ用) |

`rag/repository.py` 内部関数:

| 関数 | シグネチャ | 説明 |
|---|---|---|
| `_dedup_hits` | `(all_results: list[list[RagHit]]) -> list[RagHit]` | `use_rrf=False` 時のフォールバック。`chunk_id` をキーに先着順で重複排除し、全チャンクに `rrf_score=0.0` を付与する |

`SemanticCache` クラス:

```python
from rag.repository import SemanticCache  # rag.pipeline の __all__ には含まれない

cache = SemanticCache(max_size=100, threshold=0.92)
```

| メソッド / プロパティ | 説明 |
|---|---|
| `lookup(embedding) -> str \| None` | コサイン類似度 >= `threshold` のエントリを探してコンテキスト文字列を返す。なければ `None` |
| `put(embedding, context_str) -> None` | エントリを格納。`prune()` で `max_size` 上限管理 |
| `prune() -> None` | `max_size` 超のエントリを古い順に削除 (FIFO) |
| `size` (property) | 現在のエントリ数 (`int`); `cache.size` でアクセス |

### 1.3 エクスポートされる型

#### RawHit / MergedHit / RankedHit / RagHit

パイプライン各ステージで使うヒット型。`RagHit = RawHit | MergedHit | RankedHit` は後方互換 Union alias。

| 型 | ステージ | 必須フィールド | 追加フィールド |
|---|---|---|---|
| `RawHit` | vector_search / fts_search 直後 | `chunk_id`, `content` | `url`, `title`, `distance` (vector), `bm25_score` (FTS) |
| `MergedHit` | RRF merge 後 | `chunk_id`, `content` | RawHit 全フィールド + `rrf_score` |
| `RankedHit` | Cross-Encoder rerank 後 | `chunk_id`, `content` | MergedHit 全フィールド + `rerank_score` |

#### PipelineStageResult

各パイプラインステージの実行結果を保持するデータクラス。

| フィールド | 型 | 説明 |
|---|---|---|
| `stage` | `str` | ステージ名 |
| `success` | `bool` | 実行成否 |
| `failure_reason` | `str \| None` | 失敗時の理由 (成功時は None) |
| `elapsed_s` | `float` | 実行経過時間 (秒) |

#### LLMMessage

LLM API メッセージを表す `LLMMessage` TypedDict (`total=False`)。`AgentREPL._history` の要素型および `RagLLM._call_llm()` の引数型として使用。

```python
from rag.types import LLMMessage  # re-exports from shared.types
```

| キー | 型 | 説明 |
|---|---|---|
| `role` | `str` | メッセージロール (`"user"` / `"assistant"` / `"tool"` / `"system"`) |
| `content` | `str \| None` | テキストコンテンツ。tool_calls のみ含むメッセージでは `None` になる |
| `tool_calls` | `list[dict]` | アシスタントが要求したツール呼び出しリスト (assistant ロールのみ) |
| `tool_call_id` | `str` | ツール呼び出し応答の対応 ID (tool ロールのみ) |
| `name` | `str` | ツール名 (tool ロールのみ) |

`total=False` のため全フィールドはオプション。各ロールで実際に使うキーのみを設定。

### 1.4 設定項目

設定は 2 系統ある。

**`_get_cfg()` 経由で取得する TOML 値** (`config/common.toml` / `config/agent.toml` から初回アクセス時に遅延ロード):

| パラメータ | 設定ファイル | デフォルト | 説明 |
|---|---|---|---|
| `llm_url` | `config/agent.toml` | `http://127.0.0.1:8002/v1/chat/completions` | MQE / Rerank 用 LLM エンドポイント (`RagLLM` が `_get_cfg().get("llm_url", "")` で取得) |
| `embed_url` | `config/common.toml` | `http://127.0.0.1:8003/embedding` | 埋込 API エンドポイント (`get_embedding` が使用) |
| `mqe_n_queries` | `config/agent.toml` | `3` | MQE で生成するクエリ言い換え数 |
| `rrf_k` | `config/agent.toml` | `60` | RRF の平滑化定数 (`RagScorer.rrf_merge` に渡す) |
| `mqe_prompt_template` | `config/agent.toml` | (既定テキスト) | MQE クエリ言い換えプロンプトテンプレート。`{n_queries}` と `{query}` をプレースホルダとして使用 |
| `rerank_prompt_template` | `config/agent.toml` | (既定テキスト) | Cross-Encoder 再ランクスコアリングプロンプトテンプレート。`{query}` と `{items_text}` をプレースホルダとして使用 |

**`RagConfig` Protocol フィールド** (`shared/types.py` で定義; `AgentConfig` が実装; `RagPipeline.__init__` の `cfg` 引数として注入):

| フィールド | 型 | 説明 |
|---|---|---|
| `use_search` | `bool` | `False` のとき `augment()` は即 `""` を返す |
| `use_mqe` | `bool` | `False` のとき MQE をスキップし元クエリ 1 件のみで検索する |
| `use_rrf` | `bool` | `False` のとき RRF を `_dedup_hits` (先着順重複排除) に置き換える |
| `use_rerank` | `bool` | `False` のとき クロスエンコーダ再ランクをスキップし RRF 順で上位 `rag_top_k` 件を返す |
| `use_refiner` | `bool` | `True` のとき `_augment_refiner()` でチャンクをクエリ関連要点に圧縮する |
| `top_k_search` | `int` | `vector_search` / `fts_search` に渡すヒット上限件数 |
| `top_k_rerank` | `int` | クロスエンコーダに渡す候補件数 (`merged` をこの件数に切り詰めてから渡す) |
| `rag_top_k` | `int` | 再ランク後に返すヒット上限件数 |
| `rag_min_score` | `float` | クロスエンコーダスコアの下限フィルタ; これ未満のヒットを除外する |
| `max_chunks_per_doc` | `int` | `deduplicate_chunks` に渡す同一ドキュメントあたりの最大チャンク数 |
| `rag_service_url` | `str` | 外部 RAG サービス URL; 空文字のとき in-process パイプラインのみ使用 |
| `semantic_cache_max_size` | `int` | `SemanticCache` のエントリ上限数 |
| `semantic_cache_threshold` | `float` | `SemanticCache` のキャッシュヒット判定コサイン類似度閾値 |
| `refiner_max_tokens` | `int` | `RagLLM.refine_context` に渡す最大トークン数 |
| `refiner_max_chars_per_chunk` | `int` | `RagLLM.refine_context` に渡すチャンクあたりの最大文字数 |
| `refiner_timeout` | `float` | `RagLLM.refine_context` に渡すタイムアウト秒数 |

### 1.5 使用スクリプト

| スクリプト | 使用箇所 |
|---|---|
| `mcp/rag_pipeline/service.py` | `RagMCPService.run_pipeline()` が `RagPipeline.run()` を呼び出す。agent 側の in-process 呼び出しは削除済み |

---

